"""
Centralized logging configuration for the Data Observability Platform.
Provides JSON structured logging with file rotation and console output.
"""
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add any custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "extra_fields"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to log records."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add extra context."""
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = {"extra_fields": extra}
        return msg, kwargs


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_json: bool = True,
) -> None:
    """
    Configure centralized logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses logs/app.log
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
        enable_console: Whether to enable console logging
        enable_json: Whether to use JSON formatting
    """
    # Create logs directory if it doesn't exist
    if log_file is None:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        log_file = str(logs_dir / "app.log")
    else:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Log initial configuration
    logging.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "max_bytes": max_bytes,
            "backup_count": backup_count,
            "enable_console": enable_console,
            "enable_json": enable_json,
        },
    )


def get_logger(name: str, **context) -> ContextLogger:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name (typically __name__)
        **context: Additional context to include in all log messages
        
    Returns:
        ContextLogger instance with context
    """
    logger = logging.getLogger(name)
    return ContextLogger(logger, context)


# Utility functions
def log_with_context(logger: logging.Logger, level: str, message: str, **context) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context fields
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=context)


def parse_log_file(log_file: str, max_lines: int = 100) -> list:
    """
    Parse JSON log file and return recent log entries.
    
    Args:
        log_file: Path to log file
        max_lines: Maximum number of lines to return
        
    Returns:
        List of log entries as dictionaries
    """
    log_entries = []
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Get last max_lines
            recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            
            for line in recent_lines:
                try:
                    log_entry = json.loads(line.strip())
                    log_entries.append(log_entry)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
    except FileNotFoundError:
        pass
    
    return log_entries


def get_log_stats(log_file: str) -> Dict[str, Any]:
    """
    Get statistics about log file.
    
    Args:
        log_file: Path to log file
        
    Returns:
        Dictionary with log statistics
    """
    stats = {
        "total_lines": 0,
        "file_size_bytes": 0,
        "levels": {},
        "loggers": {},
    }
    
    try:
        log_path = Path(log_file)
        if not log_path.exists():
            return stats
        
        stats["file_size_bytes"] = log_path.stat().st_size
        
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                stats["total_lines"] += 1
                try:
                    log_entry = json.loads(line.strip())
                    
                    # Count by level
                    level = log_entry.get("level", "UNKNOWN")
                    stats["levels"][level] = stats["levels"].get(level, 0) + 1
                    
                    # Count by logger
                    logger = log_entry.get("logger", "UNKNOWN")
                    stats["loggers"][logger] = stats["loggers"].get(logger, 0) + 1
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    
    return stats
