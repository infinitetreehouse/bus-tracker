import uuid

from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import text

from bustracker.models.base import Base


class UserSchool(Base):
    __tablename__ = 'user_schools'

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'school_id',
            name='uq_user_schools_user_school'
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
        default=lambda: str(uuid.uuid4()),
    )

    user_id = Column(
        BigInteger,
        ForeignKey('users.id'),
        nullable=False
    )

    school_id = Column(
        BigInteger,
        ForeignKey('schools.id'),
        nullable=False
    )

    created_at_utc = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )

    # Probably don't need this unless we add is_active for soft deletes
    updated_at_utc = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    )
