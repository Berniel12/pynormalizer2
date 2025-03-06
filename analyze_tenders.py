import csv
import json
from collections import defaultdict, Counter
import os
import sys

def analyze_csv(file_path):
    """Analyze the unified_tenders_rows.csv file to identify normalization issues"""
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Initialize counters and statistics
    source_counts = Counter()
    null_fields_by_source = defaultdict(lambda: defaultdict(int))
    empty_fields_by_source = defaultdict(lambda: defaultdict(int))
    weird_values_by_source = defaultdict(lambda: defaultdict(list))
    total_rows = 0
    
    # Fields to analyze
    key_fields = [
        'title', 'description', 'tender_type', 'status', 'publication_date', 'deadline_date',
        'country', 'city', 'organization_name', 'buyer', 'estimated_value', 'currency',
        'procurement_method', 'document_links'
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Get the field names from the CSV
            fields = reader.fieldnames
            
            # Process each row
            for row in reader:
                total_rows += 1
                source = row['source_table']
                source_counts[source] += 1
                
                # Check for null/empty fields
                for field in key_fields:
                    if field not in row or row[field] is None:
                        null_fields_by_source[source][field] += 1
                    elif row[field].strip() == '':
                        empty_fields_by_source[source][field] += 1
                    
                    # Check for potentially weird values
                    if field in row and row[field]:
                        # Check for JSON objects in descriptions
                        if field == 'description' and (row[field].strip().startswith('{') or row[field].strip().startswith('[')):
                            weird_values_by_source[source][field].append(row[field][:100] + "...")
                        
                        # Check for weird currency values
                        if field == 'currency' and len(row[field]) > 3:
                            weird_values_by_source[source][field].append(row[field])
                        
                        # Check for valid estimated_value
                        if field == 'estimated_value' and row[field]:
                            try:
                                float(row[field])
                            except ValueError:
                                weird_values_by_source[source][field].append(row[field])
                        
                        # Check for document_links that might need normalization
                        if field == 'document_links' and row[field]:
                            try:
                                # See if it's valid JSON
                                if not row[field].startswith('[') and not row[field].startswith('{'):
                                    weird_values_by_source[source][field].append(row[field][:100] + "...")
                            except:
                                weird_values_by_source[source][field].append(row[field][:100] + "...")
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return
    
    # Print analysis results
    print(f"Total rows analyzed: {total_rows}")
    print("\nSource distribution:")
    for source, count in source_counts.most_common():
        print(f"  {source}: {count} rows ({count/total_rows*100:.1f}%)")
    
    print("\nMissing fields by source (null or not present):")
    for source in source_counts:
        print(f"\n  {source}:")
        for field in key_fields:
            null_count = null_fields_by_source[source][field]
            empty_count = empty_fields_by_source[source][field]
            if null_count > 0 or empty_count > 0:
                total = null_count + empty_count
                percent = total / source_counts[source] * 100
                print(f"    {field}: {total} ({percent:.1f}%) - {null_count} null, {empty_count} empty")
    
    print("\nPotentially problematic values:")
    for source in weird_values_by_source:
        if weird_values_by_source[source]:
            print(f"\n  {source}:")
            for field, values in weird_values_by_source[source].items():
                if values:
                    print(f"    {field}: {len(values)} issues")
                    # Print up to 3 examples
                    for i, value in enumerate(values[:3]):
                        print(f"      Example {i+1}: {value}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "unified_tenders_rows.csv"
    
    analyze_csv(file_path) 