# Local imports
from src.core.database import SessionLocal


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
