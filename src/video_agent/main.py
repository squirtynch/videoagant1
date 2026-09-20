"""AI Video Agent - Main Application Entry Point"""

import sys
import asyncio
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication

from video_agent.app.bootstrap import bootstrap_application
from video_agent.ui.windows.main_window import MainWindow
from video_agent.diagnostics.logging import setup_logging


def main():
    """Main entry point for AI Video Agent application."""
    
    # Setup logging
    log_config = setup_logging()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AI Video Agent")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("AI Video Agent Team")
    
    # Enable high DPI scaling
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # Bootstrap application services
        container = bootstrap_application(app)
        
        # Create and show main window
        window = MainWindow(container)
        window.show()
        
        # Run event loop
        sys.exit(app.exec())
        
    except Exception as e:
        log_config.logger.exception(f"Fatal application error: {e}")
        raise


if __name__ == "__main__":
    main()
