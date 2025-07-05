# Third-party imports
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Local imports
from src.core import settings


DATABASE_URL = settings.DATABASE_URL.get_secret_value()
engine = create_engine(DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Database connection test logic
def test_connection():
    try:
        connection = engine.connect()
        print('Database connection successful!')
        connection.close()
    except Exception as e:
        print(f'Database connection failed: {e}')


class Base(DeclarativeBase):
    pass


def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
    except Exception as e:
        print(f'Error creating tables: {e}')
