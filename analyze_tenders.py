import csv
import json
from collections import defaultdict, Counter
import re

# Define the fields we're interested in analyzing
FIELDS_TO_ANALYZE = [
    'source_table',  # Source of the data
    'normalized_by',  # Which normalizer was used
    'normalized_method',  # Method used for normalization
    'fallback_reason',  # Reason for fallback if any
    'title',  # Original title
    'title_english',  # Normalized title
    'description',  # Original description
    'description_english',  # Normalized description
    'organization_name',  # Original organization name
    'organization_name_english',  # Normalized organization name
    'buyer',  # Original buyer
    'buyer_english',  # Normalized buyer
    'project_name',  # Original project name
    'project_name_english',  # Normalized project name
    'language',  # Original language
]

def is_likely_truncated(field):
    """Check if a field appears to be truncated."""
    if not field:
        return False
    # Ends with ellipsis or cut-off
    return field.endswith('...') or re.search(r'\w+$', field)

def normalize_source_table(source):
    """Clean and normalize source_table values."""
    if not source:
        return "unknown"
    source = source.strip().lower()
    # Map variations to canonical names
    source_map = {
        'wb': 'wb',
        'ungm': 'ungm',
        'tedeu': 'tedeu',
        'afdb': 'afdb',
        'adb': 'adb',
        'iadb': 'iadb',
        'aiib': 'aiib',
        'afd': 'afd',
    }
    for key, value in source_map.items():
        if key in source:
            return value
    return source

def analyze_csv(csv_file):
    """Analyze the CSV file for normalization issues."""
    stats = defaultdict(Counter)
    issues = defaultdict(list)
    total_rows = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_rows += 1
            
            # Normalize and count source table
            source = normalize_source_table(row.get('source_table', ''))
            stats['sources'][source] += 1
            
            # Count normalization methods
            norm_method = row.get('normalized_method', '').strip()
            if norm_method:
                stats['normalization_methods'][norm_method] += 1
            else:
                stats['normalization_methods']['none'] += 1
            
            # Count normalizers used
            normalizer = row.get('normalized_by', '').strip()
            if normalizer:
                stats['normalizers'][normalizer] += 1
            else:
                stats['normalizers']['none'] += 1
            
            # Check for fallback reasons
            fallback = row.get('fallback_reason', '').strip()
            if fallback:
                stats['fallback_reasons'][fallback] += 1
                # Record the issue with the source
                issues[source].append({
                    'id': row.get('id', ''),
                    'source_id': row.get('source_id', ''),
                    'fallback_reason': fallback,
                    'language': row.get('language', ''),
                    'normalized_method': norm_method
                })
            
            # Check for missing normalizations
            for field in ['title', 'description', 'organization_name', 'buyer', 'project_name']:
                original = row.get(field, '').strip()
                english = row.get(f'{field}_english', '').strip()
                
                if original and not english:
                    stats['missing_normalizations'][field] += 1
                    # Record the issue
                    issues[source].append({
                        'id': row.get('id', ''),
                        'source_id': row.get('source_id', ''),
                        'issue': f'Missing {field}_english',
                        'language': row.get('language', ''),
                        'normalized_method': norm_method
                    })
            
            # Check for potential truncation in normalized fields
            for field in ['title_english', 'description_english', 'organization_name_english', 'buyer_english', 'project_name_english']:
                if is_likely_truncated(row.get(field, '')):
                    base_field = field.replace('_english', '')
                    stats['truncated_fields'][field] += 1
                    # Record the issue
                    issues[source].append({
                        'id': row.get('id', ''),
                        'source_id': row.get('source_id', ''),
                        'issue': f'Potentially truncated {field}',
                        'language': row.get('language', ''),
                        'normalized_method': norm_method
                    })
    
    return {
        'total_rows': total_rows,
        'stats': stats,
        'issues': issues
    }

def print_analysis(analysis):
    """Print the analysis results in a readable format."""
    print(f"Total rows analyzed: {analysis['total_rows']}")
    
    print("\n=== SOURCE DISTRIBUTION ===")
    for source, count in analysis['stats']['sources'].most_common():
        print(f"{source}: {count} ({count/analysis['total_rows']*100:.1f}%)")
    
    print("\n=== NORMALIZATION METHODS ===")
    for method, count in analysis['stats']['normalization_methods'].most_common():
        print(f"{method}: {count} ({count/analysis['total_rows']*100:.1f}%)")
    
    print("\n=== NORMALIZERS USED ===")
    for normalizer, count in analysis['stats']['normalizers'].most_common():
        print(f"{normalizer}: {count} ({count/analysis['total_rows']*100:.1f}%)")
    
    print("\n=== FALLBACK REASONS ===")
    for reason, count in analysis['stats']['fallback_reasons'].most_common():
        print(f"{reason}: {count} ({count/analysis['total_rows']*100:.1f}%)")
    
    print("\n=== MISSING NORMALIZATIONS ===")
    for field, count in analysis['stats']['missing_normalizations'].most_common():
        print(f"{field}_english: {count} ({count/analysis['total_rows']*100:.1f}%)")
    
    print("\n=== POTENTIALLY TRUNCATED FIELDS ===")
    for field, count in analysis['stats']['truncated_fields'].most_common():
        print(f"{field}: {count} ({count/analysis['total_rows']*100:.1f}%)")
    
    print("\n=== ISSUES BY SOURCE ===")
    for source, issues_list in analysis['issues'].items():
        if issues_list:
            issue_count = len(issues_list)
            source_total = analysis['stats']['sources'][source]
            print(f"\n{source.upper()} - {issue_count} issues ({issue_count/source_total*100:.1f}% of {source} records)")
            
            # Group issues by type
            issue_types = Counter([issue.get('issue', issue.get('fallback_reason', 'Unknown')) for issue in issues_list])
            for issue_type, count in issue_types.most_common():
                print(f"  - {issue_type}: {count} ({count/source_total*100:.1f}%)")

if __name__ == "__main__":
    csv_file = "unified_tenders_rows.csv"
    analysis = analyze_csv(csv_file)
    print_analysis(analysis) 