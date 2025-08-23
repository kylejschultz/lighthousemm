from typing import Generator
from sqlalchemy.orm import Session
from lhmm.db.session import SessionLocal

# FastAPI dependency: yield a DB session and ensure proper commit/rollback
# NOTE: Do NOT use @contextmanager here; FastAPI expects a generator function.
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
