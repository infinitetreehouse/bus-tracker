from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


_engine = None
_SessionLocal = None


def init_engine(db_uri):
    global _engine
    global _SessionLocal

    _engine = create_engine(
        db_uri,
        pool_pre_ping=True,
        pool_recycle=300
    )

    _SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_engine():
    if _engine is None:
        raise RuntimeError('db engine not initialized')
    return _engine


def get_session():
    if _SessionLocal is None:
        raise RuntimeError('db engine not initialized')
    return _SessionLocal()


def ping_db():
    with get_engine().connect() as conn:
        conn.execute(text('SELECT 1'))
