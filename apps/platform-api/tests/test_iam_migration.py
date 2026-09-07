from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from alembic import command
from alembic.config import Config


class IamMigrationTest(unittest.TestCase):
    def test_upgrade_existing_identity_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "legacy-platform.db"
            connection = sqlite3.connect(database_path)
            try:
                connection.executescript(
                    """
                    CREATE TABLE users (
                        id CHAR(32) PRIMARY KEY,
                        external_subject VARCHAR(255) NOT NULL UNIQUE,
                        email VARCHAR(255),
                        username VARCHAR(64) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        is_super_admin BOOLEAN NOT NULL,
                        platform_roles_json JSON NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    );
                    CREATE TABLE refresh_tokens (
                        id CHAR(32) PRIMARY KEY,
                        user_id CHAR(32) NOT NULL,
                        token_id VARCHAR(64) NOT NULL UNIQUE,
                        expires_at DATETIME NOT NULL,
                        revoked_at DATETIME,
                        created_at DATETIME NOT NULL
                    );
                    CREATE TABLE projects (id CHAR(32) PRIMARY KEY);
                    CREATE TABLE service_accounts (id CHAR(32) PRIMARY KEY);
                    CREATE TABLE agents (
                        id CHAR(32) PRIMARY KEY,
                        project_id CHAR(32) NOT NULL,
                        name VARCHAR(128) NOT NULL,
                        graph_id VARCHAR(128) NOT NULL,
                        langgraph_assistant_id VARCHAR(128) NOT NULL
                    );
                    CREATE UNIQUE INDEX uq_agents_project_name ON agents(project_id, name);
                    CREATE UNIQUE INDEX uq_agents_project_langgraph_assistant
                        ON agents(project_id, langgraph_assistant_id);
                    CREATE TABLE assistant_profiles (
                        id CHAR(32) PRIMARY KEY,
                        agent_id CHAR(32) NOT NULL UNIQUE,
                        status VARCHAR(32) NOT NULL,
                        config JSON NOT NULL,
                        context JSON NOT NULL,
                        metadata_json JSON NOT NULL,
                        created_by CHAR(32) NOT NULL,
                        updated_by CHAR(32) NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    );
                    CREATE TABLE operations (
                        id CHAR(32) PRIMARY KEY,
                        input_payload JSON NOT NULL
                    );
                    INSERT INTO agents VALUES (
                        '00000000000000000000000000000005',
                        '00000000000000000000000000000003',
                        'Reference Agent', 'reference_agent', 'reference_agent'
                    );
                    INSERT INTO assistant_profiles VALUES (
                        '00000000000000000000000000000006',
                        '00000000000000000000000000000005',
                        'active', '{}', '{}', '{}',
                        '00000000000000000000000000000001',
                        '00000000000000000000000000000001',
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    );
                    INSERT INTO users VALUES (
                        '00000000000000000000000000000001', 'legacy', NULL, 'legacy',
                        'hash', 'active', 0, '[]', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    );
                    INSERT INTO refresh_tokens VALUES (
                        '00000000000000000000000000000002',
                        '00000000000000000000000000000001',
                        'legacy-token', '2099-01-01 00:00:00', NULL, CURRENT_TIMESTAMP
                    );
                    """
                )
                connection.commit()
            finally:
                connection.close()

            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
            command.upgrade(config, "20260906_0006")

            connection = sqlite3.connect(database_path)
            try:
                connection.execute(
                    "INSERT INTO operations VALUES (?, ?)",
                    (
                        "00000000000000000000000000000007",
                        '{"assistant_id":"reference_agent"}',
                    ),
                )
                connection.execute(
                    """INSERT INTO runtime_runs (
                        id, project_id, thread_id, agent_key, idempotency_key,
                        request_digest, operation_id, status, active_key
                    ) VALUES (?, ?, ?, '', ?, ?, ?, ?, NULL)""",
                    (
                        "00000000000000000000000000000008",
                        "00000000000000000000000000000003",
                        "thread-legacy",
                        "key-legacy",
                        "digest-legacy",
                        "00000000000000000000000000000007",
                        "succeeded",
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            command.upgrade(config, "head")
            command.upgrade(config, "head")

            connection = sqlite3.connect(database_path)
            try:
                user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
                refresh_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(refresh_tokens)")
                }
                family_id = connection.execute(
                    "SELECT family_id FROM refresh_tokens WHERE token_id = 'legacy-token'"
                ).fetchone()[0]
                grant_table = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='service_account_project_grants'"
                ).fetchone()
                agent_indexes = {
                    tuple(
                        item[2]
                        for item in connection.execute(f"PRAGMA index_info('{row[1]}')")
                    )
                    for row in connection.execute("PRAGMA index_list(agents)")
                    if row[2]
                }
                agent_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(agents)")
                }
                profile_tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                agent_key = connection.execute(
                    "SELECT agent_key FROM runtime_runs WHERE thread_id='thread-legacy'"
                ).fetchone()[0]
                profile_count = connection.execute(
                    "SELECT COUNT(*) FROM agent_profiles"
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertTrue({"must_change_password", "failed_login_attempts", "locked_until"} <= user_columns)
            self.assertTrue({"family_id", "consumed_at"} <= refresh_columns)
            self.assertEqual(family_id, "legacy-token")
            self.assertIsNotNone(grant_table)
            self.assertIn(("project_id", "graph_id"), agent_indexes)
            self.assertNotIn("langgraph_assistant_id", agent_columns)
            self.assertIn("agent_profiles", profile_tables)
            self.assertNotIn("assistant_profiles", profile_tables)
            self.assertEqual(agent_key, "reference_agent")
            self.assertEqual(profile_count, 1)

    def test_assistant_alias_conflict_fails_before_schema_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "conflicting-platform.db"
            connection = sqlite3.connect(database_path)
            try:
                connection.executescript(
                    """
                    CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY);
                    INSERT INTO alembic_version VALUES ('20260906_0006');
                    CREATE TABLE agents (
                        id CHAR(32) PRIMARY KEY,
                        project_id CHAR(32) NOT NULL,
                        graph_id VARCHAR(128) NOT NULL,
                        langgraph_assistant_id VARCHAR(128) NOT NULL
                    );
                    CREATE TABLE assistant_profiles (
                        id CHAR(32) PRIMARY KEY,
                        agent_id CHAR(32) NOT NULL UNIQUE,
                        status VARCHAR(32) NOT NULL,
                        config JSON NOT NULL,
                        context JSON NOT NULL,
                        metadata_json JSON NOT NULL,
                        created_by CHAR(32) NOT NULL,
                        updated_by CHAR(32) NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    );
                    INSERT INTO agents VALUES ('agent-1', 'project-1', 'new', 'old');
                    """
                )
                connection.commit()
            finally:
                connection.close()

            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
            with self.assertRaisesRegex(RuntimeError, "conflicting graph_id"):
                command.upgrade(config, "head")

            connection = sqlite3.connect(database_path)
            try:
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(agents)")
                }
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            finally:
                connection.close()
            self.assertIn("langgraph_assistant_id", columns)
            self.assertIn("assistant_profiles", tables)


if __name__ == "__main__":
    unittest.main()
