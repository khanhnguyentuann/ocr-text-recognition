"""
Logging Service - Centralized logging configuration for the OCR application.

This module provides functions to set up and configure a centralized logger
that can be used across the entire application. It ensures consistent log
formatting and handling.
"""
import logging
from typing import Final

# Define a constant for the log format to ensure consistency
LOG_FORMAT: Final[str] = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'

def setup_logging() -> None:
    """
    Configures the root logger for the application.

    This function sets up a basic configuration for the logging system,
    including the logging level, format, and date format. It should be
    called once when the application starts.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance for a given module name.

    This function is a convenient wrapper around `logging.getLogger()`,
    allowing other modules to easily obtain a logger that is part of the
    application's logging hierarchy.

    Args:
        name (str): The name for the logger, which is typically the
                    `__name__` of the module where the logger is used.

    Returns:
        logging.Logger: A configured logger instance that can be used to
                        log messages.
    """
    return logging.getLogger(name)
