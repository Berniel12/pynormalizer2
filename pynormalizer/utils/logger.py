import logging
import os
import sys

# Create a logger
logger = logging.getLogger("pynormalizer")

# Set the log level based on environment, defaulting to INFO
log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logger.setLevel(log_level)

# Create console handler and set level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)

# Create file handler and set level
file_handler = logging.FileHandler("pynormalizer.log")
file_handler.setLevel(log_level)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Export logger
__all__ = ['logger'] 