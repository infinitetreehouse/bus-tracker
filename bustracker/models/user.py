import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import text

from bustracker.models.base import Base


class User(Base):
    __tablename__ = 'users'

    __table_args__ = (
        UniqueConstraint(
            'external_system',
            'external_id',
            name='uq_users_external_system_id'
        ),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    # UUID suitable for exposing via an API or URL
    public_id = Column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4())
    )

    # System where external_id comes from (PowerSchool, Google, etc.)
    external_system = Column(
        String(64),
        nullable=True
    )

    # Could be teacher number, employee ID, etc.
    external_id = Column(
        String(255),
        nullable=True
    )

    email = Column(
        String(320),
        nullable=False,
        unique=True
    )

    google_sub = Column(
        String(255),
        nullable=True,
        unique=True
    )

    full_name = Column(
        String(255),
        nullable=True
    )

    given_name = Column(
        String(255),
        nullable=True
    )

    family_name = Column(
        String(255),
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text('1')
    )

    last_login_at_utc = Column(
        DateTime,
        nullable=True
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
