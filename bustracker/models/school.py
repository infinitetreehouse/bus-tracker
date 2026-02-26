import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import text

from bustracker.models.base import Base


class School(Base):
    __tablename__ = 'schools'

    __table_args__ = (
        UniqueConstraint(
            'external_system',
            'external_id',
            name='uq_schools_external_system_id'
        ),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    public_id = Column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4())
    )

    short_name = Column(
        String(32),
        nullable=False,
        unique=True
    )

    long_name = Column(
        String(255),
        nullable=False,
        unique=True
    )

    # Canonical timezone name like America/Chicago
    timezone = Column(
        String(64),
        nullable=False
    )

    external_system = Column(
        String(64),
        nullable=True
    )

    external_id = Column(
        String(255),
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text('1')
    )

    created_at_utc = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )

    updated_at_utc = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    )
