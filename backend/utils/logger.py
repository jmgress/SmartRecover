"""Centralized logging utility for SmartRecover."""

import logging
import sys
import time
from functools import wraps
from pathlib import Path

from backend.config import config_manager


class LoggerManager:
    """Manages application-wide logging configuration."""

    _initialized: bool = False
    _loggers: dict[str, logging.Logger] = {}

    @classmethod
    def setup_logging(cls):
        """Setup logging based on configuration."""
        if cls._initialized:
            return

        logging_config = config_manager.get_logging_config()

        # Get log level (Pydantic validates it's a valid level)
        log_level = getattr(logging, logging_config.level)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(logging_config.format)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler if configured
        if logging_config.log_file:
            log_path = Path(logging_config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(logging_config.log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        cls._initialized = True

        # Log the initialization
        logger = cls.get_logger("LoggerManager")
        logger.info(f"Logging initialized with level: {logging_config.level}")
        if logging_config.enable_tracing:
            logger.info("Tracing enabled")
            logger.warning(
                "Tracing may log sensitive data - use only in development/debugging"
            )
        if logging_config.log_file:
            logger.info(f"Logging to file: {logging_config.log_file}")

    @classmethod
    def reset(cls):
        """Reset the logger manager state. Primarily for testing purposes."""
        cls._initialized = False
        cls._loggers = {}
        # Clear all handlers from root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance with the specified name."""
        if not cls._initialized:
            cls.setup_logging()

        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger

        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Name of the logger (typically __name__ of the module)

    Returns:
        A configured logger instance
    """
    return LoggerManager.get_logger(name)


def trace_execution(func):
    """Decorator to trace function execution with logging.

    Only traces if enable_tracing is True in configuration.
    Logs function entry, exit, execution time, and any exceptions.

    WARNING: This decorator logs function arguments which may contain sensitive data.
    Only enable tracing in development/debugging environments.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logging_config = config_manager.get_logging_config()

        if not logging_config.enable_tracing:
            return func(*args, **kwargs)

        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__qualname__}"

        logger.debug(f"TRACE: Entering {func_name}")
        # Note: Logging args/kwargs - may contain sensitive data
        logger.debug(f"TRACE: Args: {args}, Kwargs: {kwargs}")

        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.debug(f"TRACE: Exiting {func_name} - Elapsed: {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"TRACE: Exception in {func_name} after {elapsed:.4f}s: {e}",
                exc_info=True,
            )
            raise

    return wrapper


def trace_async_execution(func):
    """Decorator to trace async function execution with logging.

    Only traces if enable_tracing is True in configuration.
    Logs function entry, exit, execution time, and any exceptions.

    WARNING: This decorator logs function arguments which may contain sensitive data.
    Only enable tracing in development/debugging environments.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        logging_config = config_manager.get_logging_config()

        if not logging_config.enable_tracing:
            return await func(*args, **kwargs)

        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__qualname__}"

        logger.debug(f"TRACE: Entering {func_name}")
        # Note: Logging args/kwargs - may contain sensitive data
        logger.debug(f"TRACE: Args: {args}, Kwargs: {kwargs}")

        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.debug(f"TRACE: Exiting {func_name} - Elapsed: {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"TRACE: Exception in {func_name} after {elapsed:.4f}s: {e}",
                exc_info=True,
            )
            raise

    return wrapper
