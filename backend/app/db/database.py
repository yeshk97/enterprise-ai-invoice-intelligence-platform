from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# SQLite database file path.
# This creates a local database file in the project root.
DATABASE_URL = "sqlite:///./invoice_platform.db"


# Create database engine.
# The engine manages the connection between Python and the database.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# Create database session factory.
# A session is used to read/write data from/to the database.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for database models.
# Our tables will inherit from this Base.
Base = declarative_base()


def get_db():
    """
    Database dependency.

    FastAPI will use this function when an endpoint needs database access.
    It opens a database session and closes it after the request is done.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()