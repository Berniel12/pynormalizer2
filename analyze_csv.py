import csv
import json
from collections import defaultdict

# Analysis variables
sources = {}
normalized_methods = {}
fallback_reasons = {}
languages = {}
english_fields_count = defaultdict(int)
missing_fields = defaultdict(int)
normalize_status = {"normalized": 0, "not_normalized": 0}
count = 0

# Fields that should be normalized to English
english_fields = ['title', 'description', 'organization_name', 'buyer', 'project_name']

# Open and parse the CSV file
with open('unified_tenders_rows.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        count += 1
        
        # Track sources
        source = row.get('source_table')
        if source:
            sources[source] = sources.get(source, 0) + 1
        
        # Track normalization methods
        norm_method = row.get('normalized_method')
        if norm_method:
            normalized_methods[norm_method] = normalized_methods.get(norm_method, 0) + 1
        
        # Track fallback reasons
        fallback = row.get('fallback_reason')
        if fallback:
            fallback_reasons[fallback] = fallback_reasons.get(fallback, 0) + 1
        
        # Track languages
        lang = row.get('language')
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
            
        # Check if normalized
        is_normalized = bool(row.get('normalized_at'))
        if is_normalized:
            normalize_status["normalized"] += 1
        else:
            normalize_status["not_normalized"] += 1
            
        # Check English fields
        for field in english_fields:
            original_field = row.get(field)
            english_field = row.get(f'{field}_english')
            
            if original_field and english_field:
                english_fields_count[f"{field}_translated"] += 1
            elif original_field and not english_field:
                english_fields_count[f"{field}_not_translated"] += 1
                
            # Track missing fields by source
            if not original_field and source:
                missing_fields[f"{source}_{field}_missing"] += 1

# Print results
print(f'Total rows: {count}')

print('\nSource Tables:')
for s, c in sorted(sources.items(), key=lambda x: x[1], reverse=True):
    print(f'{s}: {c}')

print('\nNormalization Methods:')
for m, c in sorted(normalized_methods.items(), key=lambda x: x[1], reverse=True):
    print(f'{m}: {c}')

print('\nFallback Reasons:')
for r, c in sorted(fallback_reasons.items(), key=lambda x: x[1], reverse=True):
    print(f'{r}: {c}')

print('\nLanguages:')
for l, c in sorted(languages.items(), key=lambda x: x[1], reverse=True):
    print(f'{l}: {c}')

print('\nEnglish Fields Translation Status:')
for field, count in sorted(english_fields_count.items(), key=lambda x: x[0]):
    print(f'{field}: {count}')

print('\nMissing Fields by Source:')
for field, count in sorted(missing_fields.items(), key=lambda x: x[1], reverse=True):
    print(f'{field}: {count}')

print('\nNormalization Status:')
for status, count in normalize_status.items():
    print(f'{status}: {count}') 