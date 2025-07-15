# Logging Service - Centralized logging configuration for the OCR application.
import logging
from typing import Final

# Define a constant for the log format to ensure consistency
LOG_FORMAT: Final[str] = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'

def setup_logging() -> None:
    # Configures the root logger for the application.
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_logger(name: str) -> logging.Logger:
    # Retrieves a logger instance for a given module name.
    return logging.getLogger(name)
