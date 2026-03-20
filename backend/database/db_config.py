from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# ── Engine ────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, **engine_kwargs)

# ── Session ───────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Base for ORM models ───────────────────────────────────────────
Base = declarative_base()


# ── Dependency (used in FastAPI routes if needed) ─────────────────
def get_db():
    """
    FastAPI dependency that yields a DB session
    and ensures it is closed after the request.

    Usage in a route:
        from database.db_config import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
