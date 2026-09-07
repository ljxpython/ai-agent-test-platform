"""Enforce project-scoped agent graph keys."""

from alembic import op
import sqlalchemy as sa


revision = "20260906_0006"
down_revision = "20260905_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agents" not in inspector.get_table_names():
        return

    duplicate = bind.execute(
        sa.text(
            "SELECT project_id, graph_id FROM agents "
            "GROUP BY project_id, graph_id HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicate is not None:
        raise RuntimeError(
            "Cannot add uq_agents_project_graph_id: duplicate project_id/graph_id rows exist"
        )

    constraints = {item["name"] for item in inspector.get_unique_constraints("agents")}
    indexes = {item["name"] for item in inspector.get_indexes("agents")}
    if "uq_agents_project_graph_id" not in constraints | indexes:
        op.create_index(
            "uq_agents_project_graph_id",
            "agents",
            ["project_id", "graph_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agents" not in inspector.get_table_names():
        return
    indexes = {item["name"] for item in inspector.get_indexes("agents")}
    if "uq_agents_project_graph_id" in indexes:
        op.drop_index("uq_agents_project_graph_id", table_name="agents")
