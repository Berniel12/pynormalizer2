FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/usr/src/app:$PYTHONPATH" \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies - note the correct package names
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    supabase>=1.0.0 \
    deep-translator>=1.11.3 \
    langdetect>=1.0.9 \
    unidecode>=1.3.6 \
    pytz>=2023.3

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x apify_entry.py apify_normalize.py fix_country_normalization.py run_normalization.py

# Health check to verify Python and dependencies
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "from supabase import create_client; import deep_translator; import langdetect; import unidecode; import pytz; print('Dependencies OK')" || exit 1

# Set our entry script as entrypoint
ENTRYPOINT ["python", "apify_entry.py"]

# Default command (can be overridden)
CMD ["--batch-size", "100"]

# To run the country fix (now disabled by default), add:
# CMD ["--run-fix"] 