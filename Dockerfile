FROM python:3.9-slim

# Set working directory
WORKDIR /usr/src/app

# Set PYTHONPATH for proper module resolution
ENV PYTHONPATH="/usr/src/app:$PYTHONPATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Explicitly install deep-translator to ensure it's available
RUN pip install --no-cache-dir deep-translator>=1.11.3

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x apify_entry.py apify_normalize.py fix_country_normalization.py run_normalization.py test_normalize.py

# Set our new entry script as entrypoint
# This will run the main normalization process
ENTRYPOINT ["python", "apify_entry.py"]

# To run with specific batch size, you can override with:
# CMD ["--batch-size", "100"]
# To run the country fix (now disabled by default), add:
# CMD ["--run-fix"] 