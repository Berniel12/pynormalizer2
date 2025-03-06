from pynormalizer.models.source_models import TEDEuTender
from pynormalizer.normalizers.tedeu_normalizer import normalize_tedeu
from datetime import date
import json

# Create a sample TED EU tender
sample_tedeu = {
    "id": 12345,
    "publication_number": "TEST-12345",
    "title": "Test TED EU Tender",
    "summary": "This is a sample summary that should be used as description in the normalized tender.",
    "procedure_type": "open",
    "publication_date": date(2023, 5, 15),
    "deadline_date": date(2023, 6, 15),
    "language": "en",
    "notice_status": "active",
    "organisation_name": "Sample Organization",
    "contact_email": "contact@example.com",
    "country": "Test Country",
    "document_id": "DOC-12345",
    "links": ["https://example.com/document1", "https://example.com/document2"]
}

# Test the normalizer
try:
    print("Testing TEDEuTender normalizer with sample data...")
    normalized = normalize_tedeu(sample_tedeu)
    
    # Print the normalized result, focusing on fields relevant to our fix
    print("\nNormalized Result:")
    print(f"Title: {normalized.title}")
    print(f"Description: {normalized.description}")
    print(f"Procedure Type / Procurement Method: {normalized.procurement_method}")
    
    # Check if the summary was correctly used as description
    if normalized.description == sample_tedeu["summary"]:
        print("\n✅ SUCCESS: Summary field was correctly used as description!")
    else:
        print("\n❌ ERROR: Summary field was not correctly used as description!")
        print(f"Expected: {sample_tedeu['summary']}")
        print(f"Got: {normalized.description}")
    
    # Print full normalized tender as JSON
    print("\nFull normalized tender:")
    print(json.dumps({
        key: str(value) if isinstance(value, (date, dict)) else value
        for key, value in normalized.dict().items()
        if value is not None and key != "original_data"
    }, indent=2))
    
except Exception as e:
    print(f"Error during normalization: {e}")
    import traceback
    traceback.print_exc() 