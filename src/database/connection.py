from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from .models import Base
from ..utils import settings, app_logger


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.setup_database()
        
    def setup_database(self):
        """Setup database engine and session factory."""
        try:
            # Create engine
            if settings.database_url.startswith('sqlite'):
                # SQLite specific configuration
                self.engine = create_engine(
                    settings.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=settings.api_debug
                )
            else:
                # PostgreSQL or other databases
                self.engine = create_engine(
                    settings.database_url,
                    pool_pre_ping=True,
                    echo=settings.api_debug
                )
                
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            app_logger.info("Database connection established successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to setup database: {e}")
            raise
            
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            app_logger.info("Database tables created successfully")
        except Exception as e:
            app_logger.error(f"Failed to create tables: {e}")
            raise
            
    def drop_tables(self):
        """Drop all database tables."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            app_logger.info("Database tables dropped successfully")
        except Exception as e:
            app_logger.error(f"Failed to drop tables: {e}")
            raise
            
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            app_logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
            
    def get_session_sync(self) -> Session:
        """Get database session for dependency injection."""
        return self.SessionLocal()


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session."""
    with db_manager.get_session() as session:
        yield session


def init_database():
    """Initialize database tables."""
    db_manager.create_tables()