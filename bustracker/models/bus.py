import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import text

from bustracker.models.base import Base


class Bus(Base):
    __tablename__ = 'buses'

    __table_args__ = (
        UniqueConstraint(
            'external_system',
            'external_id',
            name='uq_buses_external_system_id',
        ),
    )

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

    # Globally unique district bus identifier/lookup key, this might just end up
    # being the same as schol_buses.display_name
    bus_code = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    external_system = Column(
        String(64),
        nullable=True,
    )

    external_id = Column(
        String(255),
        nullable=True,
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
