#!/usr/bin/env python3
"""Simple script to test imports are working correctly"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Testing imports...")

try:
    # Test importing directly from pynormalizer
    from pynormalizer import normalize_tedeu
    logger.info("✅ Successfully imported normalize_tedeu directly from pynormalizer")
except ImportError as e:
    logger.error(f"❌ Failed to import normalize_tedeu directly: {e}")
    
try:
    # Test importing from normalizers package
    from pynormalizer.normalizers import normalize_tedeu
    logger.info("✅ Successfully imported normalize_tedeu from pynormalizer.normalizers")
except ImportError as e:
    logger.error(f"❌ Failed to import normalize_tedeu from normalizers: {e}")
    
try:
    # Test importing TEDEuTender model
    from pynormalizer.models import TEDEuTender
    logger.info("✅ Successfully imported TEDEuTender model")
except ImportError as e:
    logger.error(f"❌ Failed to import TEDEuTender model: {e}")

try:
    # Test importing unified model
    from pynormalizer.models import UnifiedTender
    logger.info("✅ Successfully imported UnifiedTender model")
except ImportError as e:
    logger.error(f"❌ Failed to import UnifiedTender model: {e}")

try:
    # Test helper functions
    from pynormalizer.utils.normalizer_helpers import extract_country_from_text
    logger.info("✅ Successfully imported extract_country_from_text")
except ImportError as e:
    logger.error(f"❌ Failed to import extract_country_from_text: {e}")

logger.info("Import tests completed") 