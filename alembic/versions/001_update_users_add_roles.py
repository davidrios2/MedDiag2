"""001 — update users + add roles tables

Revision ID: 001
Revises:
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Add new columns to users ---
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("auth_provider", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("auth_subject", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("display_name", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("email_verified", sa.Boolean(), server_default="0", nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), server_default="1", nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
        # Make name nullable (identity now comes from token)
        batch_op.alter_column("name", nullable=True)

    # Unique constraint on (auth_provider, auth_subject)
    # batch_alter_table for SQLite compat
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_unique_constraint("uq_auth_identity", ["auth_provider", "auth_subject"])

    # --- Roles ---
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
    )

    # --- User-Role join ---
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    # Seed default roles
    roles_table = sa.table(
        "roles",
        sa.column("code", sa.String),
        sa.column("name", sa.Text),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(roles_table, [
        {"code": "admin",   "name": "Administrador", "description": "Acceso operativo completo"},
        {"code": "doctor",  "name": "Doctor",        "description": "Puede ver audios de pacientes asignados"},
        {"code": "patient", "name": "Paciente",      "description": "Puede subir y ver sus propios audios"},
    ])


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("roles")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_auth_identity", type_="unique")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("is_active")
        batch_op.drop_column("email_verified")
        batch_op.drop_column("display_name")
        batch_op.drop_column("auth_subject")
        batch_op.drop_column("auth_provider")
        batch_op.alter_column("name", nullable=False)
