"""Database Management using SQLAlchemy"""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

import structlog

logger = structlog.get_logger(__name__)

Base = declarative_base()


class DatabaseManager:
    """Manages SQLite database connection and sessions."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.engine = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database connection and create tables."""
        
        logger.info(f"Initializing database at {self.db_path}")
        
        # Create SQLite engine
        # Using check_same_thread=False for potential multi-threaded access
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        
        # Create all tables
        # Note: In production, use Alembic migrations instead
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
        
        self._initialized = True
    
    def get_session(self) -> Session:
        """Get a new database session."""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    def health_check(self) -> bool:
        """Perform database health check."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Database context manager
class DatabaseSession:
    """Context manager for database sessions."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        self.session = self.db_manager.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                self.session.rollback()
            else:
                try:
                    self.session.commit()
                except Exception:
                    self.session.rollback()
                    raise
            self.session.close()
