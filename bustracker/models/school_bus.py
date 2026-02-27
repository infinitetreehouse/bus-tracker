import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CHAR
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import text

from bustracker.models.base import Base


class SchoolBus(Base):
    __tablename__ = 'school_buses'

    __table_args__ = (
        UniqueConstraint(
            'school_id',
            'bus_id',
            name='uq_school_buses_school_bus',
        ),
        UniqueConstraint(
            'school_id',
            'display_name',
            name='uq_school_buses_school_display_name',
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

    school_id = Column(
        BigInteger,
        ForeignKey('schools.id'),
        nullable=False,
    )

    bus_id = Column(
        BigInteger,
        ForeignKey('buses.id'),
        nullable=False,
    )

    # What users see on tiles and checkboxes
    display_name = Column(
        String(64),
        nullable=False,
    )

    # Optional admin-friendly label ("Purple", etc.)
    color_name = Column(
        String(64),
        nullable=True,
    )

    # Standardized '#RRGGBB'
    hex_color = Column(
        CHAR(7),
        nullable=True,
    )

    sort_order = Column(
        Integer,
        nullable=True,
    )

    # Static for now; may become FK to drivers later
    driver_name = Column(
        String(128),
        nullable=True,
    )

    # Nullable by design: 1=SPED, 0/NULL=Gen Ed
    is_sped = Column(
        Boolean,
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
