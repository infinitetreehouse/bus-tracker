import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Time
from sqlalchemy import text

from bustracker.models.base import Base


class RunType(Base):
    __tablename__ = 'run_types'

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )

    public_id = Column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Could end up being the same as display_name, or maybe "ARRIVAL" for the
    # code and "Arrival" for display_name
    run_type_code = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    display_name = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    default_after_local_time = Column(
        Time,
        nullable=True,
        unique=True,
    )

    # Intentionally NO default: must be explicitly set to 1 or 0
    is_departure = Column(
        Boolean,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text('1'),
    )

    created_at_utc = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
    )

    updated_at_utc = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
    )
