# PyNormalizer

A Python-based normalizer for tender data from various sources.

## Overview

PyNormalizer is a tool for normalizing tender data from multiple sources into a standardized format. It processes raw tender data from different tables and transforms it into a unified format for easier analysis and integration.

## Features

- Normalize tender data from multiple sources
- Extract and standardize country information
- Handle date/time formats in a consistent way
- Support for different languages and translations
- Integration with PostgreSQL database for data storage

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd pynormalizer
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   export SUPABASE_DB_HOST=your_db_host
   export SUPABASE_DB_PORT=your_db_port
   export SUPABASE_DB_USER=your_db_user
   export SUPABASE_DB_PASSWORD=your_db_password
   export SUPABASE_DB_NAME=your_db_name
   ```

## Usage

### Command Line Options

The normalizer can be run using the following command-line options:

```
python -m pynormalizer.apify_normalize [options]
```

Options:
- `--tables`: Comma-separated list of tables to normalize (default: all tables with normalizers)
- `--limit`: Maximum number of tenders to process per table (default: 5000)
- `--skip-normalized`: Skip already normalized tenders (default: True)
- `--process-all`: Process all tenders regardless of normalization status (default: False)
- `--single-id`: Process a single tender by ID
- `--single-table`: Table name for single tender processing (used with `--single-id`)

### Examples

1. Normalize all unnormalized tenders from all tables:
   ```
   python -m pynormalizer.apify_normalize
   ```

2. Normalize tenders from specific tables:
   ```
   python -m pynormalizer.apify_normalize --tables="tedeu_tenders,dgmarket_tenders"
   ```

3. Process a specific tender:
   ```
   python -m pynormalizer.apify_normalize --single-id="12345" --single-table="tedeu_tenders"
   ```

## Database Structure

The normalizer expects the following database structure:

- Source tables with tender data (table names configurable)
- A `unified_tenders` table where normalized data is stored

## Adding New Normalizers

To add support for a new data source:

1. Create a new normalizer file in `pynormalizer/normalizers/`
2. Implement the normalizer function that transforms raw data to the unified format
3. Add the normalizer to the `NORMALIZERS` dictionary in `pynormalizer/normalizers/__init__.py`
4. Add the table mapping in the `TABLE_MAPPING` dictionary

## Troubleshooting

If you encounter issues with the normalization process:

1. Check that all required environment variables are set
2. Verify database connection parameters
3. Check database permissions
4. Look for errors in the logs

## License

[Specify your license here]