from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# ── Engine ────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    echo=False,          # Set True to see SQL logs in terminal (debug mode)
    pool_pre_ping=True,  # Checks connection health before using from pool
)

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