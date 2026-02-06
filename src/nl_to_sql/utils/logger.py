"""
Centralized logging configuration for NL-to-SQL Pipeline
"""
import logging
import sys
from nl_to_sql.config import Config

def setup_logger(name: str) -> logging.Logger:
    """Setup and return a logger with the given name"""
    logger = logging.getLogger(name)

    # Only add handlers if not already present
    if not logger.handlers:
        logger.setLevel(Config.LOG_LEVEL)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Default logger
logger = setup_logger("nl_to_sql")
