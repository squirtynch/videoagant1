"""Main Application Window"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

import structlog

logger = structlog.get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with navigation."""
    
    def __init__(self, container):
        super().__init__()
        
        self.container = container
        self.logger = structlog.get_logger(__name__)
        
        self.setWindowTitle("AI Video Agent")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar navigation
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #f5f5f5;")
        main_layout.addWidget(self.content_stack)
        
        # Add pages
        self._add_pages()
        
        # Apply styles
        self._apply_styles()
        
        self.logger.info("Main window initialized")
    
    def _create_sidebar(self) -> QWidget:
        """Create sidebar navigation."""
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(10)
        
        # App title
        title = QLabel("AI VIDEO AGENT")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4CAF50; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", 0),
            ("Projects", 1),
            ("Short Maker", 2),
            ("Brief-to-Edit", 3),
            ("AI Assistant", 4),
            ("Settings", 5),
        ]
        
        for text, index in nav_buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    text-align: left;
                    padding-left: 10px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                }
                QPushButton:pressed {
                    background-color: #4CAF50;
                }
            """)
            btn.clicked.connect(lambda checked, i=index: self.content_stack.setCurrentIndex(i))
            layout.addWidget(btn)
        
        # Spacer
        layout.addStretch()
        
        return sidebar
    
    def _add_pages(self):
        """Add content pages to the stack."""
        
        # Page 0: Dashboard
        dashboard = self._create_dashboard_page()
        self.content_stack.addWidget(dashboard)
        
        # Page 1: Projects (placeholder)
        projects = self._create_placeholder_page("Projects", "Project management coming soon")
        self.content_stack.addWidget(projects)
        
        # Page 2: Short Maker (placeholder)
        short_maker = self._create_placeholder_page("Short Maker", "Short creation tool coming soon")
        self.content_stack.addWidget(short_maker)
        
        # Page 3: Brief-to-Edit (placeholder)
        brief_edit = self._create_placeholder_page("Brief-to-Edit", "Brief processing coming soon")
        self.content_stack.addWidget(brief_edit)
        
        # Page 4: AI Assistant (placeholder)
        assistant = self._create_placeholder_page("AI Assistant", "AI assistant coming soon")
        self.content_stack.addWidget(assistant)
        
        # Page 5: Settings (placeholder)
        settings = self._create_placeholder_page("Settings", "Settings panel coming soon")
        self.content_stack.addWidget(settings)
    
    def _create_dashboard_page(self) -> QWidget:
        """Create dashboard page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Welcome header
        header = QLabel("Welcome to AI Video Agent")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #333;")
        layout.addWidget(header)
        
        subtitle = QLabel("AI-powered video editing automation for DaVinci Resolve")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)
        
        action_buttons = [
            ("+ New Project", "Create a new project"),
            ("Create Shorts", "Generate shorts from long videos"),
            ("Edit from Brief", "Create edit from text brief"),
        ]
        
        for text, tooltip in action_buttons:
            btn = QPushButton(text)
            btn.setFixedSize(200, 60)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            actions_layout.addWidget(btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        # Status section
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("System Status")
        status_title.setFont(QFont("Arial", 14, QFont.Bold))
        status_layout.addWidget(status_title)
        
        # Status items (placeholders)
        status_items = [
            ("DaVinci Resolve", "NOT DETECTED"),
            ("AI Providers", "NOT CONFIGURED"),
            ("FFmpeg", "NOT DETECTED"),
            ("Database", "OK"),
        ]
        
        for name, status in status_items:
            item_layout = QHBoxLayout()
            name_label = QLabel(name)
            status_label = QLabel(status)
            
            color = "#4CAF50" if status == "OK" else "#ff9800" if "NOT" in status else "#f44336"
            status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            item_layout.addWidget(name_label)
            item_layout.addStretch()
            item_layout.addWidget(status_label)
            status_layout.addLayout(item_layout)
        
        layout.addWidget(status_frame)
        
        return page
    
    def _create_placeholder_page(self, title: str, message: str) -> QWidget:
        """Create a placeholder page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel(f"{title}\n\n{message}")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: #999;")
        layout.addWidget(label)
        
        return page
    
    def _apply_styles(self):
        """Apply application-wide styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Application closing")
        
        if self.container:
            try:
                self.container.shutdown()
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")
        
        event.accept()
