#!/bin/bash
# Script to run full normalization of all tenders from all sources

echo "Starting full normalization process..."
echo "This will process ALL tenders from ALL sources"
echo "Progress will be reported every 100 tenders"
echo ""

# Create a timestamp for the output file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="normalization_report_${TIMESTAMP}.json"

# Run the normalization script with the full option
python run_normalization.py --full --output $OUTPUT_FILE

echo ""
echo "Normalization process completed"
echo "Report saved to $OUTPUT_FILE" 