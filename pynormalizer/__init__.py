"""PyNormalizer - A Python framework for normalizing tender data from various sources."""

__version__ = "1.0.0"

# Import key functions to make them available at package level
try:
    # This makes normalize_all_tenders directly available from pynormalizer package
    from .main import normalize_all_tenders
    
    # Import normalize_tedeu directly to make it available at package level
    from .normalizers.tedeu_normalizer import normalize_tedeu
    
    __all__ = [
        'normalize_all_tenders',
        'normalize_tedeu'
    ]
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing from main or normalizers: {e}")
