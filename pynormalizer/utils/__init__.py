"""Utility modules for the PyNormalizer package.

This package contains various utility functions and helpers for normalizing tender data.
"""

# Don't import modules directly at the package level to avoid circular imports
# Instead, users should import specific modules as needed

# For convenience, define what's available in this package
__all__ = [
    # From normalizer_helpers
    'extract_organization_and_buyer',
    'ensure_country',
    'log_before_after',
    'clean_price',
    'clean_date',
    
    # From db
    'get_connection',
    'get_supabase_client',
    'fetch_rows',
    
    # From translation
    'setup_translation_models'
]

# For backward compatibility, provide a warning about imports
import logging
logger = logging.getLogger(__name__)
logger.info("Use explicit imports from pynormalizer.utils submodules instead of importing from pynormalizer.utils directly")
