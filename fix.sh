#!/bin/bash
# Fix AIIB normalizer issues

FILE="pynormalizer/normalizers/aiib_normalizer.py"

# Make a backup
cp "$FILE" "${FILE}.bak"
echo "Created backup at ${FILE}.bak"

# Fix 1: ensure_country parameter name
sed -i.old1 's/country=country_string/country_value=country_string/g' "$FILE"
echo "Fixed ensure_country parameter name"

# Fix 2: determine_normalized_method call
sed -i.old2 's/normalized_method = determine_normalized_method(extraction_methods)/normalized_method = determine_normalized_method({"source_table": "aiib", "extraction_methods": extraction_methods})/g' "$FILE"
echo "Fixed determine_normalized_method call"

echo "All fixes applied to $FILE" 