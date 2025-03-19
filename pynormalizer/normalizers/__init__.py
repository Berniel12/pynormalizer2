"""Normalizer module collection for various tender data sources"""

# Import normalizers individually with separate try-except blocks to avoid cascading failures
__all__ = []

# Import ADB normalizer
try:
    from .adb_normalizer import normalize_adb
    __all__.append('normalize_adb')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing adb_normalizer: {e}")

# Import AFD normalizer
try:
    from .afd_normalizer import normalize_afd
    __all__.append('normalize_afd')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing afd_normalizer: {e}")

# Import AFDB normalizer
try:
    from .afdb_normalizer import normalize_afdb
    __all__.append('normalize_afdb')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing afdb_normalizer: {e}")

# Import AIIB normalizer
try:
    from .aiib_normalizer import normalize_aiib
    __all__.append('normalize_aiib')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing aiib_normalizer: {e}")

# Import IADB normalizer
try:
    from .iadb_normalizer import normalize_iadb
    __all__.append('normalize_iadb')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing iadb_normalizer: {e}")

# Import Sam.gov normalizer
try:
    from .samgov_normalizer import normalize_samgov
    __all__.append('normalize_samgov')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing samgov_normalizer: {e}")

# Import TED EU normalizer
try:
    from .tedeu_normalizer import normalize_tedeu
    __all__.append('normalize_tedeu')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing tedeu_normalizer: {e}")

# Import UNGM normalizer
try:
    from .ungm_normalizer import normalize_ungm
    __all__.append('normalize_ungm')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing ungm_normalizer: {e}")

# Import World Bank normalizer
try:
    from .wb_normalizer import normalize_wb
    __all__.append('normalize_wb')
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing wb_normalizer: {e}")
