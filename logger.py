from loguru import logger
import sys

# Unified log format string
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"

# Remove default logger configuration
logger.remove()

# Configure Loguru for stdout (DEBUG+), stderr (ERROR+), and file output (DEBUG+), all with unified format
logger.add(sys.stdout, level="DEBUG", format=log_format, colorize=True)
logger.add(sys.stderr, level="ERROR", format=log_format, colorize=True)
logger.add("logs/app.log", rotation="1 MB", level="DEBUG", format=log_format)

# Alias for easy import
LOG = logger

# Make LOG available for import
__all__ = ["LOG"]