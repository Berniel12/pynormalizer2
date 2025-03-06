FROM python:3.9-slim

# Set working directory
WORKDIR /usr/src/app

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Explicitly install deep-translator to ensure it's available
RUN pip install --no-cache-dir deep-translator>=1.11.3

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x apify_normalize.py run_normalization.py test_normalize.py

# Set script as entrypoint without forcing test mode
# This will respect the input JSON settings for testMode
ENTRYPOINT ["python", "apify_normalize.py"]

# To run with specific batch size, you can override with:
# CMD ["--batch-size", "100"] 