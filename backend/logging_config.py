"""Logging configuration for SmartRecover."""
import logging
import sys
import os
import json
from typing import Optional
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add trace_id if present
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class TraceAdapter(logging.LoggerAdapter):
    """Logger adapter that adds trace_id to all log records."""
    
    def process(self, msg, kwargs):
        """Process log message to add trace_id."""
        # Get trace_id from extra or use the one from adapter
        extra = kwargs.get("extra", {})
        if "trace_id" not in extra and "trace_id" in self.extra:
            extra["trace_id"] = self.extra["trace_id"]
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    log_level: Optional[str] = None,
    json_format: Optional[bool] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting
        log_file: Optional file path for logging
    """
    # Get configuration from environment or defaults
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    if json_format is None:
        json_format = os.getenv("LOG_JSON", "false").lower() in ("true", "1", "yes")
    
    if log_file is None:
        log_file = os.getenv("LOG_FILE")
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Log the logging configuration
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "extra_fields": {
                "log_level": log_level,
                "json_format": json_format,
                "log_file": log_file
            }
        }
    )


def get_logger(name: str, trace_id: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with optional trace_id support.
    
    Args:
        name: Logger name (usually __name__)
        trace_id: Optional trace ID for request tracing
    
    Returns:
        Logger or TraceAdapter if trace_id is provided
    """
    logger = logging.getLogger(name)
    
    if trace_id:
        return TraceAdapter(logger, {"trace_id": trace_id})
    
    return logger
