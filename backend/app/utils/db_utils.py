"""Database utility functions and helpers"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal, engine, Base


def check_database_connection() -> bool:
    """Check if database connection is working
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except SQLAlchemyError as e:
        print(f"Database connection failed: {e}")
        return False


def create_all_tables() -> None:
    """Create all tables in the database"""
    try:
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully")
    except SQLAlchemyError as e:
        print(f"Error creating tables: {e}")
        raise


def drop_all_tables() -> None:
    """Drop all tables in the database (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped successfully")
    except SQLAlchemyError as e:
        print(f"Error dropping tables: {e}")
        raise


def get_db_session() -> Session:
    """Get a new database session
    
    Returns:
        Session: SQLAlchemy session
    """
    return SessionLocal()
