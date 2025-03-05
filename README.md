# PyNormalizer

A data normalization pipeline for tender data from multiple sources.

## Overview

This package normalizes tender data from 9 different source tables into a unified format:

- ADB - Asian Development Bank
- AFD - Agence Française de Développement
- AFDB - African Development Bank
- AIIB - Asian Infrastructure Investment Bank
- IADB - Inter-American Development Bank
- SAM.gov - System for Award Management (US)
- TED.eu - Tenders Electronic Daily (EU)
- UNGM - United Nations Global Marketplace
- WB - World Bank

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Direct PostgreSQL Connection

```python
from pynormalizer.main import normalize_all_tenders

# Configure database connection
db_config = {
    "dbname": "YOUR_DB_NAME",
    "user": "YOUR_DB_USER",
    "password": "YOUR_DB_PASSWORD",
    "host": "YOUR_DB_HOST",
    "port": 5432
}

# Run the normalization process
normalize_all_tenders(db_config)
```

### Supabase Connection

The package can also connect to Supabase using environment variables:

```python
import os
from pynormalizer.main import normalize_all_tenders

# Set Supabase environment variables
os.environ["SUPABASE_URL"] = "https://your-project-id.supabase.co"
os.environ["SUPABASE_KEY"] = "your-supabase-key"

# Run normalization with empty config (will use env vars instead)
normalize_all_tenders({})
```

### Running on Apify

For Apify deployment, use the included `apify_normalize.py` script:

1. Set the following environment variables in your Apify actor:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. Use `apify_normalize.py` as your main script.

### Command-line Scripts

The package includes several executable scripts:

#### 1. apify_normalize.py

Main script for running the normalization process on Apify:

```bash
# Run in test mode (2 records per source)
./apify_normalize.py --test

# Run in production mode with specific tables
./apify_normalize.py --tables adb wb --batch-size 100

# Run in production mode for all tables
./apify_normalize.py
```

#### 2. test_normalize.py

Script for testing normalization with a small sample:

```bash
# Test with 2 records per source (default)
./test_normalize.py

# Test with 5 records per source and save report
./test_normalize.py --limit 5 --output test_report.json

# Test specific tables
./test_normalize.py --tables adb wb
```

#### 3. run_normalization.py

General-purpose script for running normalization:

```bash
# Run with config file
./run_normalization.py --config config.json

# Run with limit
./run_normalization.py --limit 10
```

## Features

- Normalizes data from 9 different tender sources
- Maps source-specific fields to a unified schema
- Performs lightweight translation of non-English fields using deep-translator
- Handles database upserts with conflict resolution
- Supports both direct PostgreSQL and Supabase connections
- Detailed logging for before/after comparison
- Test mode for quality evaluation
- Translation statistics tracking

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison log

## Translation

The package uses the lightweight `deep-translator` library for translating non-English content:

- Automatically detects source language
- Translates titles, descriptions, and other key fields to English
- Uses Google Translate API without requiring API keys
- Falls back to a dictionary-based approach for common terms if translation fails
- Significantly smaller footprint compared to other translation libraries
- No large model downloads required

## Docker Support

The package includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t pynormalizer .

# Run in test mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer

# Run in production mode
docker run -e SUPABASE_URL=your-url -e SUPABASE_KEY=your-key pynormalizer --batch-size 100
```

## Logging

The package generates several log files:

- `apify_normalize.log` - Main log for Apify script
- `pynormalizer.log` - Core normalization log
- `test_normalize.log` - Test script log
- `normalization_comparison.log` - Detailed before/after comparison