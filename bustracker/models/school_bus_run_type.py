import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import text

from bustracker.models.base import Base


class SchoolBusRunType(Base):
    __tablename__ = 'school_bus_run_types'

    __table_args__ = (
        UniqueConstraint(
            'school_bus_id',
            'run_type_id',
            name='uq_school_bus_run_types_bus_run_type',
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

    school_bus_id = Column(
        BigInteger,
        ForeignKey('school_buses.id'),
        nullable=False,
    )

    run_type_id = Column(
        BigInteger,
        ForeignKey('run_types.id'),
        nullable=False,
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
