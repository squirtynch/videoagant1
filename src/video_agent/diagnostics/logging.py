"""Structured Logging Configuration"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory


class LogConfig:
    """Logging configuration holder."""
    
    def __init__(self, logger, log_file: Optional[Path] = None):
        self.logger = logger
        self.log_file = log_file


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> LogConfig:
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    
    Returns:
        LogConfig with configured logger
    """
    
    # Determine log file path
    if log_file is None:
        # Default to AppData/logs directory
        import sys
        if sys.platform == "win32":
            log_dir = Path.home() / "AppData" / "Local" / "AIVideoAgent" / "logs"
        else:
            log_dir = Path.home() / ".local" / "share" / "AIVideoAgent" / "logs"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"video_agent_{timestamp}.log"
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib, log_level.upper(), structlog.stdlib.INFO).level
        ),
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create formatter for file output
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        ],
    )
    
    # Create formatter for console output
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
        ],
    )
    
    # Get standard library logger
    import logging
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)
    
    # Create application logger
    logger = structlog.get_logger("video_agent")
    
    return LogConfig(logger, log_file)
