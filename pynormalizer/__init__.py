"""PyNormalizer - A Python framework for normalizing tender data from various sources."""

__version__ = "1.0.0"

# Import key functions to make them available at package level
try:
    # This makes normalize_all_tenders directly available from pynormalizer package
    from .main import normalize_all_tenders
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing from main: {e}")
