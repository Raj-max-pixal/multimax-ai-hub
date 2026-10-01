"""Add user profile About text and case-insensitive usernames.

Revision ID: 8b1f7f3a9c21
Revises: 3ff0865da455
Create Date: 2026-10-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b1f7f3a9c21"
down_revision: Union[str, None] = "3ff0865da455"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    duplicates = connection.execute(
        sa.text(
            "SELECT lower(username), count(*) "
            "FROM users GROUP BY lower(username) HAVING count(*) > 1"
        )
    ).fetchall()
    if duplicates:
        names = ", ".join(row[0] for row in duplicates[:10])
        raise RuntimeError(
            "Cannot enforce case-insensitive usernames; resolve duplicate names first: "
            f"{names}"
        )

    op.add_column(
        "users",
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("users", "bio", server_default=None)
    op.create_index(
        "uq_users_username_lower",
        "users",
        [sa.text("lower(username)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_username_lower", table_name="users")
    op.drop_column("users", "bio")
