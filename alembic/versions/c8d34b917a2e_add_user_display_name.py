from alembic import op
import sqlalchemy as sa

revision = "c8d34b917a2e"
down_revision = "67af9298f95a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=120), nullable=True))
    op.execute(
        "UPDATE users SET name = LEFT(SPLIT_PART(email, '@', 1), 120) WHERE name IS NULL"
    )


def downgrade() -> None:
    op.drop_column("users", "name")