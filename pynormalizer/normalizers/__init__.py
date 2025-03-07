"""Normalizer module collection for various tender data sources"""

# Use relative imports to avoid circular dependencies
try:
    from .adb_normalizer import normalize_adb
    from .afd_normalizer import normalize_afd
    from .afdb_normalizer import normalize_afdb
    from .aiib_normalizer import normalize_aiib
    from .iadb_normalizer import normalize_iadb
    from .samgov_normalizer import normalize_samgov
    from .tedeu_normalizer import normalize_tedeu
    from .ungm_normalizer import normalize_ungm
    from .wb_normalizer import normalize_wb
    
    # Export all normalizers at the package level
    __all__ = [
        'normalize_adb',
        'normalize_afd',
        'normalize_afdb',
        'normalize_aiib',
        'normalize_iadb',
        'normalize_samgov',
        'normalize_tedeu',
        'normalize_ungm',
        'normalize_wb'
    ]
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing normalizers: {e}")
