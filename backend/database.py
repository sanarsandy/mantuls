"""
Database setup - SQLAlchemy + SQLite (upgradeable to PostgreSQL via DATABASE_URL env var)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./mantuls.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)

# Enable WAL journal mode for SQLite so multiple workers/readers don't block
# each other. Harmless no-op for PostgreSQL.
if _is_sqlite:
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _set_wal_mode(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA synchronous=NORMAL")
        dbapi_conn.execute("PRAGMA busy_timeout=5000")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session and closes it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on app startup."""
    # Import models so Base.metadata knows about them
    from models.whiteboard import WhiteboardRoom, WhiteboardSnapshot, WhiteboardMember  # noqa
    Base.metadata.create_all(bind=engine)
