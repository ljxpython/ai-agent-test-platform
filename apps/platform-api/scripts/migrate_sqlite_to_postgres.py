from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

TABLES_IN_LOAD_ORDER = [
    "tenants",
    "users",
    "projects",
    "project_members",
    "refresh_tokens",
    "agents",
    "assistant_profiles",
    "audit_logs",
]

JSON_COLUMNS = {
    "assistant_profiles": {"config", "context", "metadata_json"},
    "audit_logs": {"metadata_json"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", default="data/archive/agent_platform_v3_migrated_20260307.db"
    )
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def source_rows(
    source_path: Path, table: str
) -> tuple[list[str], list[dict[str, Any]]]:
    conn = sqlite3.connect(source_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            return columns, []
        columns = list(rows[0].keys())
        payload = [{key: row[key] for key in columns} for row in rows]
        return columns, payload
    finally:
        conn.close()


def normalize_value(table: str, column: str, value: Any) -> Any:
    if column in JSON_COLUMNS.get(table, set()):
        if value is None or value == "":
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value
    if column == "is_super_admin" and value is not None:
        return bool(value)
    return value


def destination_columns(engine, table: str) -> list[str]:
    query = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :table_name
        ORDER BY ordinal_position
        """
    )
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query, {"table_name": table}).fetchall()]


def truncate_tables(engine) -> None:
    statement = (
        "TRUNCATE TABLE "
        + ", ".join(TABLES_IN_LOAD_ORDER)
        + " RESTART IDENTITY CASCADE"
    )
    with engine.begin() as conn:
        conn.execute(text(statement))


def insert_rows(
    engine, table: str, columns: list[str], rows: list[dict[str, Any]]
) -> None:
    if not rows:
        return
    placeholders = ", ".join(f":{column}" for column in columns)
    column_list = ", ".join(columns)
    statement = text(f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})")
    payload = []
    for row in rows:
        payload.append(
            {
                column: normalize_value(table, column, row.get(column))
                for column in columns
            }
        )
    with engine.begin() as conn:
        conn.execute(statement, payload)


def main() -> None:
    args = parse_args()
    load_dotenv()
    source_path = Path(args.source)
    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not source_path.exists():
        raise SystemExit(f"source sqlite db not found: {source_path}")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    engine = create_engine(database_url, pool_pre_ping=True)
    table_payloads: dict[str, tuple[list[str], list[dict[str, Any]]]] = {}
    for table in TABLES_IN_LOAD_ORDER:
        source_cols, source_data = source_rows(source_path, table)
        dest_cols = destination_columns(engine, table)
        columns = [column for column in source_cols if column in dest_cols]
        table_payloads[table] = (columns, source_data)

    for table in TABLES_IN_LOAD_ORDER:
        _, rows = table_payloads[table]
        print(f"{table}: {len(rows)} rows")

    if args.dry_run:
        return

    truncate_tables(engine)
    for table in TABLES_IN_LOAD_ORDER:
        columns, rows = table_payloads[table]
        insert_rows(engine, table, columns, rows)


if __name__ == "__main__":
    main()
