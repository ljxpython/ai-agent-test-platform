# pyright: reportMissingImports=false, reportMissingModuleSource=false
from __future__ import annotations

"""usecase_workflow_agent 的端到端 smoke 脚本（走 LangGraph API）。

它解决的问题：
- 服务跑起来之后，我们希望用一个“确定性”的输入，验证：
  1) LangGraph dev server 可用（assistants/threads/runs API 正常）。
  2) usecase_workflow_agent 能识别到“已 review 的候选用例”，触发 HITL（人工确认）中断。
  3) 对中断给出 approve 决策后，Agent 能把用例持久化到 interaction-data-service。

整体流程（非常关键，建议先看 _run_smoke）：
1) 通过 LangGraph SDK 找到目标 assistant（默认 usecase_workflow_agent）。
2) 创建 thread，并把 thread state "seed" 成“已 review，等待用户确认”的阶段：
   - 塞入一条 tool message（record_usecase_review），其 content 是 review snapshot JSON。
   - 再塞入一条 user message，明确确认现在可以 persist。
3) 创建 run 并 join 等待结果，期望出现 __interrupt__（HITL）。
4) 用 command.resume + decisions=[approve] 继续 run。
5) 通过 interaction-data-service 的 REST API 拉取持久化结果并做断言。

运行前提：
- 本地已启动 `langgraph dev --config runtime_service/langgraph.json --port 8123`
- interaction-data-service 在 8081 可访问（或设置 INTERACTION_DATA_SERVICE_URL）。

常用环境变量：
- LANGGRAPH_API_URL / INTERACTION_DATA_SERVICE_URL
- SMOKE_ASSISTANT_NAME / SMOKE_MODEL_ID / SMOKE_TIMEOUT_SECONDS
- SMOKE_INCLUDE_PDF=1  # 可选：附带一个 test_data 下的 PDF 走多模态路径
"""

import asyncio
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import langgraph_sdk
import requests

from runtime_service.devtools.multimodal_frontend_compat import (
    file_path_to_frontend_content_block,
)


DEFAULT_LANGGRAPH_URL = "http://127.0.0.1:8123"
DEFAULT_INTERACTION_DATA_SERVICE_URL = "http://127.0.0.1:8081"
DEFAULT_ASSISTANT_NAME = "usecase_workflow_agent"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_PDF_TIMEOUT_SECONDS = 180
EXPECTED_USECASE_TITLES = (
    "Login succeeds with valid credentials",
    "Login fails with invalid password",
)


def _env_flag(name: str, default: bool = False) -> bool:
    # 从环境变量读取布尔开关：1/true/yes/on 视为 True。
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _format_for_console(value: Any, *, ascii_safe: bool = False) -> str:
    """格式化终端输出。

    - 默认 ascii_safe=False：优先输出可读中文。
    - 需要“保险”时可把 ascii_safe=True，让非 ASCII 变成 \\uXXXX。
    """

    text = str(value)
    if not ascii_safe:
        return text
    return text.encode("ascii", "backslashreplace").decode("ascii")


@dataclass(frozen=True)
class SmokeConfig:
    # 把所有可调参数集中收口，便于通过环境变量控制。
    langgraph_url: str = os.getenv("LANGGRAPH_API_URL", DEFAULT_LANGGRAPH_URL)
    interaction_data_service_url: str = os.getenv(
        "INTERACTION_DATA_SERVICE_URL", DEFAULT_INTERACTION_DATA_SERVICE_URL
    )
    assistant_name: str = os.getenv("SMOKE_ASSISTANT_NAME", DEFAULT_ASSISTANT_NAME)
    model_id: str | None = (os.getenv("SMOKE_MODEL_ID") or "").strip() or None
    timeout_seconds: int = int(
        os.getenv("SMOKE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    )
    include_pdf_attachment: bool = _env_flag("SMOKE_INCLUDE_PDF", default=False)


def _resolve_timeout_seconds(include_pdf_attachment: bool) -> int:
    raw_timeout = os.getenv("SMOKE_TIMEOUT_SECONDS")
    if raw_timeout is not None and raw_timeout.strip():
        return int(raw_timeout)
    if include_pdf_attachment:
        return DEFAULT_PDF_TIMEOUT_SECONDS
    return DEFAULT_TIMEOUT_SECONDS


def _load_config_from_env() -> SmokeConfig:
    include_pdf_attachment = _env_flag("SMOKE_INCLUDE_PDF", default=False)
    return SmokeConfig(
        langgraph_url=os.getenv("LANGGRAPH_API_URL", DEFAULT_LANGGRAPH_URL),
        interaction_data_service_url=os.getenv(
            "INTERACTION_DATA_SERVICE_URL", DEFAULT_INTERACTION_DATA_SERVICE_URL
        ),
        assistant_name=os.getenv("SMOKE_ASSISTANT_NAME", DEFAULT_ASSISTANT_NAME),
        model_id=(os.getenv("SMOKE_MODEL_ID") or "").strip() or None,
        timeout_seconds=_resolve_timeout_seconds(include_pdf_attachment),
        include_pdf_attachment=include_pdf_attachment,
    )


def _build_seed_usecases() -> list[dict[str, Any]]:
    # 这里用固定的、可预期的用例数据作为 smoke 输入，避免 LLM 生成的不确定性影响断言。
    return [
        {
            "title": EXPECTED_USECASE_TITLES[0],
            "description": "User signs in successfully with valid credentials.",
            "preconditions": ["The user account exists and is active."],
            "steps": [
                "Open the login page.",
                "Enter a valid username and password.",
                "Submit the login form.",
            ],
            "expected_results": [
                "The user reaches the home page.",
                "A valid authenticated session is created.",
            ],
            "coverage_points": ["Happy path authentication"],
            "status": "active",
        },
        {
            "title": EXPECTED_USECASE_TITLES[1],
            "description": "User sees a validation error when the password is wrong.",
            "preconditions": ["The user account exists and is active."],
            "steps": [
                "Open the login page.",
                "Enter a valid username and an invalid password.",
                "Submit the login form.",
            ],
            "expected_results": [
                "Login is rejected.",
                "An invalid credentials message is shown.",
            ],
            "coverage_points": ["Authentication failure handling"],
            "status": "active",
        },
    ]


def _build_review_snapshot(project_id: str) -> dict[str, Any]:
    # 构造一个“已 review 完成、可等待用户确认”的快照，模拟上游流程已经做完的阶段。
    usecases = _build_seed_usecases()
    return {
        "workflow_type": "usecase_generation",
        "stage": "reviewed_candidate_usecases",
        "summary": "Reviewed login use cases are ready for explicit confirmation.",
        "persistable": True,
        "next_action": "await_user_confirmation",
        "payload": {
            "workflow_id": None,
            "project_id": project_id,
            "candidate_usecase_count": len(usecases),
            "deficiency_count": 0,
            "candidate_usecases": {
                "workflow_id": None,
                "project_id": project_id,
                "usecases": usecases,
            },
            "review_report": {
                "summary": "The seeded candidate use cases cover the happy path and a key failure path.",
                "candidate_usecases": usecases,
                "deficiencies": [],
                "strengths": [
                    "The smoke input is deterministic.",
                    "Both success and validation failure paths are covered.",
                ],
                "revision_suggestions": [],
                "ready_for_confirmation": True,
            },
            "revised_usecases": None,
        },
    }


def _build_user_prompt(project_id: str) -> str:
    return (
        "Smoke request\n"
        f"- project_id: {project_id}\n"
        "- reviewed candidate use cases: 2\n"
        "- intent: explicitly confirm persistence for the reviewed use cases\n"
        "I explicitly confirm persistence for the reviewed use cases in this project. "
        "Please save them now."
    )


def _find_optional_pdf() -> Path | None:
    # 从 test_data 里找一个 PDF（如果存在），用于可选的多模态链路验证。
    test_data_dir = Path(__file__).resolve().parent.parent / "test_data"
    pdf_paths = sorted(test_data_dir.glob("*.pdf"))
    return pdf_paths[0] if pdf_paths else None


def _build_user_message(prompt: str, include_pdf_attachment: bool) -> dict[str, Any]:
    # 根据开关决定消息形态：纯文本 / 文本 + 附件 blocks。
    if not include_pdf_attachment:
        return {"role": "user", "content": prompt}

    pdf_path = _find_optional_pdf()
    if pdf_path is None:
        return {"role": "user", "content": prompt}

    return {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            file_path_to_frontend_content_block(pdf_path),
        ],
    }


async def _resolve_assistant(client: Any, assistant_name: str) -> dict[str, Any]:
    # assistants.search 返回一批已注册的 assistant。这里支持用 assistant_id/name/graph_id 任意命中。
    assistants = await client.assistants.search()
    for assistant in assistants:
        if assistant.get("assistant_id") == assistant_name:
            return assistant
        if assistant.get("name") == assistant_name:
            return assistant
        if assistant.get("graph_id") == assistant_name:
            return assistant
    raise RuntimeError(f"assistant_not_found:{assistant_name}")


async def _join_run(client: Any, thread_id: str, run_id: str, timeout_seconds: int) -> Any:
    # join 是一个“等待 run 完成”的长轮询；这里加超时，避免卡死。
    return await asyncio.wait_for(
        client.runs.join(thread_id, run_id),
        timeout=timeout_seconds,
    )


def _extract_interrupts(
    run_result: Any, thread_state: Mapping[str, Any]
) -> list[dict[str, Any]]:
    # LangGraph 的中断信息可能出现在：
    # - run_result["__interrupt__"]（较新/直观）
    # - thread_state.tasks[].interrupts（某些版本/实现路径）
    if isinstance(run_result, dict):
        raw = run_result.get("__interrupt__")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]

    tasks = thread_state.get("tasks")
    if not isinstance(tasks, list):
        return []

    collected: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        interrupts = task.get("interrupts")
        if not isinstance(interrupts, list):
            continue
        collected.extend(item for item in interrupts if isinstance(item, dict))
    return collected


def _first_error(run_result: Any, thread_state: Mapping[str, Any]) -> str | None:
    # 同上：错误信息可能在 run_result["__error__"] 或 thread_state.tasks[].error。
    if isinstance(run_result, dict):
        raw_error = run_result.get("__error__")
        if isinstance(raw_error, dict):
            error_name = str(raw_error.get("error") or "error").strip()
            message = str(raw_error.get("message") or "").strip()
            return f"{error_name}: {message}" if message else error_name

    tasks = thread_state.get("tasks")
    if not isinstance(tasks, list):
        return None
    for task in tasks:
        if not isinstance(task, dict):
            continue
        error = task.get("error")
        if error:
            return str(error)
    return None


def _verify_persisted_usecases(config: SmokeConfig, project_id: str) -> tuple[int, list[str]]:
    # 最终验证：interaction-data-service 侧应该能查到该 project_id 下落库的用例。
    response = requests.get(
        f"{config.interaction_data_service_url.rstrip('/')}/api/usecase-generation/use-cases",
        params={"project_id": project_id},
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    items = payload.get("items")
    if not isinstance(items, list):
        raise RuntimeError("invalid_usecase_list_response")

    titles: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("project_id") != project_id:
            raise RuntimeError("project_id_mismatch_in_persisted_results")
        title = item.get("title")
        if isinstance(title, str) and title.strip():
            titles.append(title.strip())

    return len(items), titles


async def _run_smoke(config: SmokeConfig) -> int:
    # 主流程：创建 thread -> seed 状态 -> run -> 期待中断 -> resume approve -> 校验落库。
    client = langgraph_sdk.get_client(url=config.langgraph_url)
    project_id = str(uuid.uuid4())
    thread_id = ""
    initial_run_id = ""
    resume_run_id = ""
    interrupt_detected = False
    persisted_count = 0
    resume_error: str | None = None

    try:
        assistant = await _resolve_assistant(client, config.assistant_name)
        assistant_id = str(assistant.get("assistant_id") or config.assistant_name)

        thread = await client.threads.create(
            metadata={
                "graph_id": config.assistant_name,
                "smoke_script": "smoke_usecase_workflow_langgraph_api",
                "project_id": project_id,
            }
        )
        thread_id = str(thread.get("thread_id") or "")
        if not thread_id:
            raise RuntimeError("missing_thread_id")

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

        # 第一次 run：期望走到 HITL 中断（需要用户 approve）。
        run_one = await client.runs.create(
            thread_id,
            assistant_id,
            input={
                "messages": [
                    _build_user_message(prompt, config.include_pdf_attachment)
                ]
            },
            config=(
                {"configurable": {"model_id": config.model_id}}
                if config.model_id
                else None
            ),
        )
        initial_run_id = str(run_one.get("run_id") or "")
        first_result = await _join_run(
            client,
            thread_id,
            initial_run_id,
            config.timeout_seconds,
        )
        first_state = await client.threads.get_state(thread_id)

        interrupts = _extract_interrupts(first_result, first_state)
        interrupt_detected = bool(interrupts)
        if not interrupt_detected:
            error = _first_error(first_result, first_state)
            raise RuntimeError(error or "missing_hitl_interrupt")

        # 第二次 run：resume，并对中断决策给出 approve。
        run_two = await client.runs.create(
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
        resume_run_id = str(run_two.get("run_id") or "")
        second_result = await _join_run(
            client,
            thread_id,
            resume_run_id,
            config.timeout_seconds,
        )
        second_state = await client.threads.get_state(thread_id)
        resume_error = _first_error(second_result, second_state)

        # 校验落库：数量 & title 必须包含预期用例。
        persisted_count, persisted_titles = _verify_persisted_usecases(config, project_id)
        expected_titles = {str(title) for title in EXPECTED_USECASE_TITLES}
        missing_titles = sorted(expected_titles.difference(set(persisted_titles)))
        if persisted_count < len(EXPECTED_USECASE_TITLES):
            raise RuntimeError("persisted_usecase_count_too_low")
        if missing_titles:
            raise RuntimeError(
                f"missing_expected_titles:{','.join(sorted(missing_titles))}"
            )

        print(f"thread_id={_format_for_console(thread_id)}")
        print(f"run_id={_format_for_console(initial_run_id or 'n/a')}")
        print(f"resume_run_id={_format_for_console(resume_run_id or 'n/a')}")
        print(f"project_id={_format_for_console(project_id)}")
        print(f"interrupt_detected={'yes' if interrupt_detected else 'no'}")
        print(f"persisted_count={persisted_count}")
        if resume_error:
            print(f"resume_result_error={_format_for_console(resume_error)}")
        else:
            print("resume_result_error=none")
        print("summary=PASS")
        return 0
    finally:
        await client.aclose()


def main() -> int:
    config = _load_config_from_env()
    try:
        try:
            stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
            stderr_reconfigure = getattr(sys.stderr, "reconfigure", None)
            if callable(stdout_reconfigure):
                stdout_reconfigure(encoding="utf-8", errors="replace")
            if callable(stderr_reconfigure):
                stderr_reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        return asyncio.run(_run_smoke(config))
    except Exception as exc:
        print(f"summary=FAIL")
        print(f"error={_format_for_console(exc)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
