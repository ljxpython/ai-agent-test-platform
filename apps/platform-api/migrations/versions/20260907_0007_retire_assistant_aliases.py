"""Retire duplicated Assistant storage aliases."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision = "20260907_0007"
down_revision = "20260906_0006"
branch_labels = None
depends_on = None


def _object(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        if isinstance(decoded, Mapping):
            return decoded
    return {}


def _profile_row(row: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(row)
    for key in ("id", "agent_id", "created_by", "updated_by"):
        if isinstance(normalized[key], str):
            normalized[key] = UUID(normalized[key])
    for key in ("config", "context", "metadata_json"):
        normalized[key] = dict(_object(normalized[key]))
    for key in ("created_at", "updated_at"):
        if isinstance(normalized[key], str):
            normalized[key] = datetime.fromisoformat(normalized[key])
    return normalized


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    run_backfill: list[tuple[object, str]] = []
    if {"runtime_runs", "operations"} <= tables:
        run_columns = {column["name"] for column in inspector.get_columns("runtime_runs")}
        operation_columns = {column["name"] for column in inspector.get_columns("operations")}
        if {"id", "operation_id", "agent_key"} <= run_columns and {
            "id",
            "input_payload",
        } <= operation_columns:
            rows = bind.execute(
                sa.text(
                    "SELECT r.id, o.input_payload FROM runtime_runs r "
                    "JOIN operations o ON o.id = r.operation_id "
                    "WHERE r.agent_key IS NULL OR TRIM(r.agent_key) = ''"
                )
            ).all()
            for run_id, input_payload in rows:
                agent_key = str(_object(input_payload).get("assistant_id") or "").strip()
                if not agent_key:
                    raise RuntimeError(
                        f"Cannot backfill runtime_runs.agent_key for run {run_id}"
                    )
                run_backfill.append((run_id, agent_key))

    agent_backfill: list[tuple[object, str]] = []
    if "agents" in tables:
        agent_columns = {column["name"] for column in inspector.get_columns("agents")}
        if "langgraph_assistant_id" in agent_columns:
            rows = bind.execute(
                sa.text("SELECT id, graph_id, langgraph_assistant_id FROM agents")
            ).all()
            targets: set[tuple[str, str]] = set()
            projects = dict(
                bind.execute(sa.text("SELECT id, project_id FROM agents")).all()
            )
            for agent_id, graph_id, legacy_id in rows:
                graph_key = str(graph_id or "").strip()
                legacy_key = str(legacy_id or "").strip()
                if graph_key and legacy_key and graph_key != legacy_key:
                    raise RuntimeError(
                        f"Agent {agent_id} has conflicting graph_id and langgraph_assistant_id"
                    )
                target = graph_key or legacy_key
                if not target:
                    raise RuntimeError(f"Agent {agent_id} has no graph key")
                identity = (str(projects[agent_id]), target)
                if identity in targets:
                    raise RuntimeError(
                        "Cannot retire Assistant alias: duplicate project_id/graph_id"
                    )
                targets.add(identity)
                if not graph_key:
                    agent_backfill.append((agent_id, target))

    profile_columns = (
        "id",
        "agent_id",
        "status",
        "config",
        "context",
        "metadata_json",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    profile_rows: list[dict[str, object]] = []
    profile_agent_ids: set[str] = set()
    for table_name in ("assistant_profiles", "agent_profiles"):
        if table_name not in tables:
            continue
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing = set(profile_columns) - columns
        if missing:
            raise RuntimeError(
                f"Cannot migrate {table_name}: missing columns {sorted(missing)}"
            )
        rows = bind.execute(
            sa.text(f"SELECT {', '.join(profile_columns)} FROM {table_name}")
        ).mappings()
        for row in rows:
            agent_id = str(row["agent_id"])
            if agent_id in profile_agent_ids:
                raise RuntimeError(f"Duplicate Agent profile for agent {agent_id}")
            profile_agent_ids.add(agent_id)
            profile_rows.append(_profile_row(row))

    for run_id, agent_key in run_backfill:
        bind.execute(
            sa.text("UPDATE runtime_runs SET agent_key = :agent_key WHERE id = :run_id"),
            {"agent_key": agent_key, "run_id": run_id},
        )
    for agent_id, graph_key in agent_backfill:
        bind.execute(
            sa.text("UPDATE agents SET graph_id = :graph_id WHERE id = :agent_id"),
            {"graph_id": graph_key, "agent_id": agent_id},
        )

    for table_name in ("assistant_profiles", "agent_profiles"):
        if table_name in tables:
            op.drop_table(table_name)

    if "agents" in tables and "langgraph_assistant_id" in {
        column["name"] for column in sa.inspect(bind).get_columns("agents")
    }:
        constraints = {
            item["name"] for item in sa.inspect(bind).get_unique_constraints("agents")
        }
        indexes = {item["name"] for item in sa.inspect(bind).get_indexes("agents")}
        with op.batch_alter_table("agents") as batch:
            if "uq_agents_project_langgraph_assistant" in constraints:
                batch.drop_constraint(
                    "uq_agents_project_langgraph_assistant", type_="unique"
                )
            elif "uq_agents_project_langgraph_assistant" in indexes:
                batch.drop_index("uq_agents_project_langgraph_assistant")
            batch.drop_column("langgraph_assistant_id")

    op.create_table(
        "agent_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id"),
    )
    if profile_rows:
        profile_table = sa.table(
            "agent_profiles",
            sa.column("id", sa.Uuid()),
            sa.column("agent_id", sa.Uuid()),
            sa.column("status", sa.String(length=32)),
            sa.column("config", sa.JSON()),
            sa.column("context", sa.JSON()),
            sa.column("metadata_json", sa.JSON()),
            sa.column("created_by", sa.Uuid()),
            sa.column("updated_by", sa.Uuid()),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(profile_table, profile_rows)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "agent_profiles" in tables and "assistant_profiles" not in tables:
        op.rename_table("agent_profiles", "assistant_profiles")
    columns = {column["name"] for column in sa.inspect(bind).get_columns("agents")}
    if "langgraph_assistant_id" not in columns:
        with op.batch_alter_table("agents") as batch:
            batch.add_column(
                sa.Column(
                    "langgraph_assistant_id",
                    sa.String(length=128),
                    nullable=False,
                    server_default="",
                )
            )
        bind.execute(
            sa.text("UPDATE agents SET langgraph_assistant_id = graph_id")
        )
