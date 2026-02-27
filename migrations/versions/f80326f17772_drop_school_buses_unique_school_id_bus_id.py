"""drop school_buses unique school_id bus_id

Revision ID: f80326f17772
Revises: 1cc2ddaa35ce
Create Date: 2026-02-27 08:30:46.631612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f80326f17772'
down_revision: Union[str, Sequence[str], None] = '1cc2ddaa35ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        'uq_school_buses_school_bus',
        'school_buses',
        type_='unique',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint(
        'uq_school_buses_school_bus',
        'school_buses',
        ['school_id', 'bus_id'],
    )
