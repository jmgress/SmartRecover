"""Logging configuration and utilities for SmartRecover application."""
import os
import sys
import logging
import functools
import time
import asyncio
from pathlib import Path
from typing import Optional, Callable, Any
from logging.handlers import RotatingFileHandler


# Default logging configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_FILE = "smartrecover.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


class LoggerManager:
    """Manages logging configuration for the SmartRecover application."""
    
    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger manager."""
        if not self._initialized:
            self._configured_loggers = set()
            self._log_level = logging.INFO
            self._verbose = False
            self._log_file: Optional[Path] = None
            self._file_handler: Optional[RotatingFileHandler] = None
            self._console_handler: Optional[logging.StreamHandler] = None
            LoggerManager._initialized = True
    
    def configure(
        self,
        log_level: str = DEFAULT_LOG_LEVEL,
        verbose: bool = False,
        log_file: Optional[str] = None,
        log_to_console: bool = True,
        log_format: str = DEFAULT_LOG_FORMAT,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT
    ):
        """
        Configure the logging system.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            verbose: Enable verbose logging (sets level to DEBUG)
            log_file: Path to log file (None to disable file logging)
            log_to_console: Enable console logging
            log_format: Log message format
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup log files to keep
        """
        # Determine effective log level
        if verbose:
            self._log_level = logging.DEBUG
            self._verbose = True
        else:
            self._log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Set up console handler
        if log_to_console:
            if self._console_handler:
                logging.getLogger().removeHandler(self._console_handler)
            
            self._console_handler = logging.StreamHandler(sys.stdout)
            self._console_handler.setLevel(self._log_level)
            formatter = logging.Formatter(log_format)
            self._console_handler.setFormatter(formatter)
        
        # Set up file handler
        if log_file:
            self._log_file = Path(log_file)
            # Create log directory if it doesn't exist
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self._file_handler:
                logging.getLogger().removeHandler(self._file_handler)
            
            self._file_handler = RotatingFileHandler(
                self._log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            self._file_handler.setLevel(self._log_level)
            formatter = logging.Formatter(log_format)
            self._file_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self._log_level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Add configured handlers
        if self._console_handler:
            root_logger.addHandler(self._console_handler)
        if self._file_handler:
            root_logger.addHandler(self._file_handler)
        
        # Log the configuration
        logger = self.get_logger("logging_config")
        logger.info(f"Logging configured: level={logging.getLevelName(self._log_level)}, verbose={self._verbose}")
        if self._log_file:
            logger.info(f"File logging enabled: {self._log_file}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance with the given name.
        
        Args:
            name: Logger name (typically __name__ from the calling module)
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        # Only configure if not already configured
        if name not in self._configured_loggers:
            logger.setLevel(self._log_level)
            self._configured_loggers.add(name)
        
        return logger
    
    def is_verbose(self) -> bool:
        """Check if verbose logging is enabled."""
        return self._verbose
    
    def get_log_level(self) -> int:
        """Get the current log level."""
        return self._log_level


# Singleton instance
_logger_manager = LoggerManager()


def configure_logging(
    log_level: str = DEFAULT_LOG_LEVEL,
    verbose: bool = False,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    log_format: str = DEFAULT_LOG_FORMAT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT
):
    """
    Configure the logging system for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbose: Enable verbose logging (sets level to DEBUG)
        log_file: Path to log file (None to disable file logging)
        log_to_console: Enable console logging
        log_format: Log message format
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    _logger_manager.configure(
        log_level=log_level,
        verbose=verbose,
        log_file=log_file,
        log_to_console=log_to_console,
        log_format=log_format,
        max_bytes=max_bytes,
        backup_count=backup_count
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        Configured logger instance
    """
    return _logger_manager.get_logger(name)


def is_verbose() -> bool:
    """Check if verbose logging is enabled."""
    return _logger_manager.is_verbose()


def trace_execution(func: Callable) -> Callable:
    """
    Decorator to trace function execution with entry/exit logging and timing.
    
    Args:
        func: Function to trace
        
    Returns:
        Wrapped function with tracing
    """
    logger = get_logger(func.__module__)
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(f"→ Entering {func_name}")
        
        if is_verbose():
            # Log arguments in verbose mode (be careful with sensitive data)
            safe_args = _sanitize_args(args)
            safe_kwargs = _sanitize_kwargs(kwargs)
            logger.debug(f"  Arguments: args={safe_args}, kwargs={safe_kwargs}")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"← Exiting {func_name} (took {elapsed:.3f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"✗ Exception in {func_name} after {elapsed:.3f}s: {e}", exc_info=True)
            raise
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(f"→ Entering {func_name}")
        
        if is_verbose():
            # Log arguments in verbose mode
            safe_args = _sanitize_args(args)
            safe_kwargs = _sanitize_kwargs(kwargs)
            logger.debug(f"  Arguments: args={safe_args}, kwargs={safe_kwargs}")
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"← Exiting {func_name} (took {elapsed:.3f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"✗ Exception in {func_name} after {elapsed:.3f}s: {e}", exc_info=True)
            raise
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def _sanitize_args(args: tuple) -> tuple:
    """Sanitize arguments to avoid logging sensitive information."""
    # Convert complex objects to simple string representations
    return tuple(
        _sanitize_value(arg) for arg in args
    )


def _sanitize_kwargs(kwargs: dict) -> dict:
    """Sanitize keyword arguments to avoid logging sensitive information."""
    sensitive_keys = {'password', 'token', 'api_key', 'secret', 'apikey', 'key'}
    return {
        k: '***REDACTED***' if any(s in k.lower() for s in sensitive_keys) else _sanitize_value(v)
        for k, v in kwargs.items()
    }


def _sanitize_value(value: Any) -> Any:
    """Sanitize a single value for logging."""
    # For complex objects, just show type and maybe id
    if hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, list, dict, tuple)):
        return f"<{type(value).__name__} object>"
    elif isinstance(value, (list, tuple)) and len(value) > 10:
        return f"<{type(value).__name__} with {len(value)} items>"
    elif isinstance(value, dict) and len(value) > 10:
        return f"<dict with {len(value)} items>"
    elif isinstance(value, str) and len(value) > 100:
        return f"{value[:97]}..."
    return value
