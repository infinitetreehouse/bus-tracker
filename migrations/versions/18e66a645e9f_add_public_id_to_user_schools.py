"""add public_id to user_schools

Revision ID: 18e66a645e9f
Revises: 29097541305d
Create Date: 2026-02-27 16:01:34.034891

"""
import uuid

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18e66a645e9f'
down_revision: Union[str, Sequence[str], None] = '29097541305d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add as nullable first (safe for existing rows), use raw SQL instead of
    # op.add_column() so we can specify "AFTER id"
    op.execute(
        sa.text(
            'ALTER TABLE user_schools '
            'ADD COLUMN public_id VARCHAR(36) NULL '
            'AFTER id'
        )
    )

    # 2) Backfill existing rows with Python UUIDs (safe deterministic literals)
    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT id FROM user_schools')).fetchall()

    for (row_id,) in rows:
        conn.execute(
            sa.text(
                'UPDATE user_schools '
                'SET public_id = :public_id '
                'WHERE id = :id'
            ),
            {
                'public_id': str(uuid.uuid4()),
                'id': row_id,
            },
        )

    # 3) Now enforce NOT NULL
    op.alter_column(
        'user_schools',
        'public_id',
        existing_type=sa.String(length=36),
        nullable=False,
    )

    # 4) Add unique constraint
    op.create_unique_constraint(
        'public_id',
        'user_schools',
        ['public_id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'public_id',
        'user_schools',
        type_='unique',
    )
    op.drop_column('user_schools', 'public_id')
