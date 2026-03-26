# pyright: reportMissingImports=false, reportMissingModuleSource=false
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _maybe_load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


_maybe_load_local_env()

import langgraph_sdk  # noqa: E402

from runtime_service.devtools.smoke_usecase_workflow_langgraph_api import (  # noqa: E402
    DEFAULT_PDF_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    EXPECTED_USECASE_TITLES,
    SmokeConfig,
    _build_review_snapshot,
    _build_user_message,
    _build_user_prompt,
    _extract_interrupts,
    _first_error,
    _join_run,
    _load_config_from_env,
    _resolve_assistant,
    _resolve_timeout_seconds,
    _verify_persisted_usecases,
)


def test_resolve_timeout_seconds_keeps_plain_smoke_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMOKE_TIMEOUT_SECONDS", raising=False)
    assert _resolve_timeout_seconds(False) == DEFAULT_TIMEOUT_SECONDS


def test_resolve_timeout_seconds_uses_pdf_default_when_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SMOKE_TIMEOUT_SECONDS", raising=False)
    assert _resolve_timeout_seconds(True) == DEFAULT_PDF_TIMEOUT_SECONDS


def test_load_config_from_env_prefers_explicit_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_INCLUDE_PDF", "1")
    monkeypatch.setenv("SMOKE_TIMEOUT_SECONDS", "95")

    config = _load_config_from_env()

    assert config.include_pdf_attachment is True
    assert config.timeout_seconds == 95


def _check_localhost_prerequisites(config: SmokeConfig) -> None:
    try:
        requests.get(config.langgraph_url, timeout=3)
    except requests.RequestException as exc:
        pytest.skip(f"LangGraph API is not reachable at {config.langgraph_url}: {exc}")

    try:
        response = requests.get(
            f"{config.interaction_data_service_url.rstrip('/')}/api/usecase-generation/use-cases",
            params={"project_id": str(uuid.uuid4())},
            timeout=config.timeout_seconds,
        )
    except requests.RequestException as exc:
        pytest.skip(
            "interaction-data-service is not reachable at "
            f"{config.interaction_data_service_url}: {exc}"
        )
    else:
        response.raise_for_status()


async def _run_smoke(config: SmokeConfig) -> None:
    client = langgraph_sdk.get_client(url=config.langgraph_url)
    project_id = str(uuid.uuid4())

    print(f"[smoke] langgraph_url={config.langgraph_url}")
    print(
        "[smoke] interaction_data_service_url="
        f"{config.interaction_data_service_url}"
    )
    print(f"[smoke] project_id={project_id}")

    try:
        assistant = await _resolve_assistant(client, config.assistant_name)
        assistant_id = str(assistant.get("assistant_id") or config.assistant_name)
        print(f"[smoke] assistant_resolved={assistant_id}")

        thread = await client.threads.create(
            metadata={
                "graph_id": config.assistant_name,
                "smoke_test": "test_usecase_workflow_langgraph_api_smoke",
                "project_id": project_id,
            }
        )
        thread_id = str(thread.get("thread_id") or "")
        assert thread_id, "LangGraph API did not return a thread_id"
        print(f"[smoke] thread_created={thread_id}")

        snapshot = _build_review_snapshot(project_id)
        prompt = _build_user_prompt(project_id)
        await client.threads.update_state(
            thread_id,
            {
                "current_stage": "awaiting_user_confirmation",
                "latest_snapshot": snapshot,
                "ready_for_persist": True,
                "messages": [
                    {
                        "type": "tool",
                        "name": "record_usecase_review",
                        "tool_call_id": "seed_review_snapshot",
                        "content": json.dumps(snapshot, ensure_ascii=False),
                    }
                ],
            },
        )
        print("[smoke] reviewed_snapshot_seeded")

        initial_run = await client.runs.create(
            thread_id,
            assistant_id,
            input={
                "messages": [
                    _build_user_message(prompt, include_pdf_attachment=False)
                ]
            },
            config=(
                {"configurable": {"model_id": config.model_id}}
                if config.model_id
                else None
            ),
        )
        initial_run_id = str(initial_run.get("run_id") or "")
        assert initial_run_id, "LangGraph API did not return an initial run_id"
        print(f"[smoke] run_started={initial_run_id}")

        first_result = await _join_run(
            client,
            thread_id,
            initial_run_id,
            config.timeout_seconds,
        )
        first_state = await client.threads.get_state(thread_id)
        first_error = _first_error(first_result, first_state)
        interrupts = _extract_interrupts(first_result, first_state)

        assert first_error is None, f"initial run failed before interrupt: {first_error}"
        assert interrupts, "expected a HITL interrupt before persistence"
        print(f"[smoke] interrupt_detected={len(interrupts)}")

        resume_run = await client.runs.create(
            thread_id,
            assistant_id,
            input=None,
            command={"resume": {"decisions": [{"type": "approve"}]}},
            config=(
                {"configurable": {"model_id": config.model_id}}
                if config.model_id
                else None
            ),
        )
        resume_run_id = str(resume_run.get("run_id") or "")
        assert resume_run_id, "LangGraph API did not return a resume run_id"
        print(f"[smoke] resume_sent={resume_run_id}")

        second_result = await _join_run(
            client,
            thread_id,
            resume_run_id,
            config.timeout_seconds,
        )
        second_state = await client.threads.get_state(thread_id)
        second_error = _first_error(second_result, second_state)
        second_interrupts = _extract_interrupts(second_result, second_state)
        next_steps = second_state.get("next")

        print(f"[smoke] resume_next={next_steps}")
        assert second_error is None, f"resume run left an error behind: {second_error}"
        assert not second_interrupts, "resume run should finish without another interrupt"
        assert not next_steps, f"resume run did not end cleanly: next={next_steps}"

        persisted_count, persisted_titles = _verify_persisted_usecases(config, project_id)
        print(f"[smoke] persisted_count={persisted_count}")
        print(f"[smoke] persisted_titles={sorted(persisted_titles)}")

        assert persisted_count == len(EXPECTED_USECASE_TITLES)
        assert sorted(persisted_titles) == sorted(EXPECTED_USECASE_TITLES)
        print("[smoke] PASS")
    finally:
        await client.aclose()


def test_usecase_workflow_langgraph_api_smoke() -> None:
    config = SmokeConfig(include_pdf_attachment=False)
    _check_localhost_prerequisites(config)
    asyncio.run(_run_smoke(config))
