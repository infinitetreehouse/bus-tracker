import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CHAR
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import text

from bustracker.models.base import Base


class StatusType(Base):
    __tablename__ = 'status_types'

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

    status_type_code = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    display_name = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    color_name = Column(
        String(64),
        nullable=False,
    )

    hex_color = Column(
        CHAR(7),
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
