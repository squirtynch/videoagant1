"""Application Bootstrap and Dependency Injection"""

from typing import Dict, Any
from PySide6.QtWidgets import QApplication

from video_agent.app.config import AppSettings, load_settings
from video_agent.storage.database import DatabaseManager
from video_agent.diagnostics.logging import setup_logging


class ApplicationContainer:
    """Dependency injection container for application services."""
    
    def __init__(self):
        self.settings: AppSettings = None
        self.logger = None
        self.db_manager: DatabaseManager = None
        self.services: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self, qt_app: QApplication):
        """Initialize application components."""
        
        # Setup logging
        log_config = setup_logging()
        self.logger = log_config.logger
        self.logger.info("Initializing AI Video Agent application")
        
        # Load settings
        self.settings = load_settings()
        self.settings.ensure_directories()
        self.logger.info(f"Settings loaded from {self.settings.get_storage_base}")
        
        # Initialize database
        self.db_manager = DatabaseManager(self.settings.get_database_path)
        self.db_manager.initialize()
        self.logger.info("Database initialized")
        
        # Register services (to be implemented in subsequent phases)
        # self.services['project_service'] = ProjectService(self.db_manager)
        # self.services['media_service'] = MediaService(self.db_manager)
        # etc.
        
        self._initialized = True
        self.logger.info("Application initialization complete")
        
        return self
    
    def get_service(self, name: str):
        """Get a registered service by name."""
        if not self._initialized:
            raise RuntimeError("Application not initialized")
        
        if name not in self.services:
            raise KeyError(f"Service '{name}' not found")
        
        return self.services[name]
    
    def register_service(self, name: str, service: Any):
        """Register a service."""
        self.services[name] = service
    
    def shutdown(self):
        """Cleanup application resources."""
        self.logger.info("Shutting down application")
        
        if self.db_manager:
            self.db_manager.close()
        
        self.logger.info("Application shutdown complete")


def bootstrap_application(qt_app: QApplication) -> ApplicationContainer:
    """Bootstrap the application and return the container."""
    container = ApplicationContainer()
    container.initialize(qt_app)
    return container
