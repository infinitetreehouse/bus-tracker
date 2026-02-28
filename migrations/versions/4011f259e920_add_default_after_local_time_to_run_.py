"""add default_after_local_time to run_types

Revision ID: 4011f259e920
Revises: 18e66a645e9f
Create Date: 2026-02-28 06:12:16.407106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4011f259e920'
down_revision: Union[str, Sequence[str], None] = '18e66a645e9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column right after display_name, use raw SQL to specify position
    op.execute(
        sa.text(
            'ALTER TABLE run_types '
            'ADD COLUMN default_after_local_time TIME NULL '
            'AFTER display_name'
        )
    )

    # Add unique constraint (allow multiple NULLs)
    op.create_unique_constraint(
        'default_after_local_time',
        'run_types',
        ['default_after_local_time'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'default_after_local_time',
        'run_types',
        type_='unique',
    )
    op.drop_column('run_types', 'default_after_local_time')
