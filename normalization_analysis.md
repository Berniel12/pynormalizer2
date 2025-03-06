# Normalization Analysis by Source

This document provides an analysis of how each source is normalized into the UnifiedTender model, highlighting potential issues and improvement opportunities.

## UnifiedTender Model Fields

The UnifiedTender model contains the following key fields:
- `title` (required)
- `description`
- `tender_type`
- `status`
- `publication_date`
- `deadline_date`
- `country`
- `city`
- `organization_name`
- `buyer`
- `estimated_value`
- `currency`
- `procurement_method`
- `document_links`

## Analysis by Source

### TED EU Normalizer

**Fields Mapping:**
- `title` → `title`
- `summary` → `description` ✅ (fixed)
- `procedure_type` → `procurement_method`
- `publication_date` → `publication_date`
- `deadline_date` → `deadline_date`
- `country` → `country`
- `organisation_name` → `organization_name`

**Issues Fixed:**
- Changed `description` field to correctly use `summary` since TED EU model doesn't have a description field.
- Added proper checks with `hasattr()` to avoid attribute errors.

**Potential Improvements:**
- Add more robust extraction of financial information from the summary field.
- Improve organization name extraction by checking in multiple fields.

### World Bank (WB) Normalizer

**Fields Mapping:**
- `title` → `title`
- `description` → `description`
- `tender_type` → `tender_type`
- `publication_date` → `publication_date`
- `deadline` → `deadline_date`
- `country` → `country`
- `contact_organization` → `organization_name`
- `document_links` → `document_links`
- `procurement_method` → `procurement_method`

**Issues Fixed:**
- Fixed regex pattern matching using `match` vs `search`.
- Improved handling of None values in iterations.

**Potential Improvements:**
- Enhance extraction of city information from addresses.
- Better handling of project-related fields.

### AFD Normalizer

**Fields Mapping:**
- `notice_title` → `title`
- `notice_content` → `description`
- `publication_date` → `publication_date`
- `deadline` → `deadline_date`
- `country` → `country`
- `city_locality` → `city`
- `agency` → `organization_name`
- `buyer` → `buyer`

**Issues Fixed:**
- Added check for existence of `contract_amount` attribute before accessing it.
- Improved financial information extraction from descriptions.

**Potential Improvements:**
- Extract more procurement method information from notice content.
- Better language detection for multi-language tenders.

### ADB Normalizer

**Fields Mapping:**
- `notice_title` → `title`
- `description` → `description`
- `publication_date` → `publication_date`
- `due_date` → `deadline_date`
- `country` → `country`
- `sector` → `sector`
- `loan_number` → Referenced in `reference_number`
- `pdf_url` → Added to `document_links`

**Potential Improvements:**
- Extract city information from descriptions.
- Better extraction of organization names and buyer information.
- Improve financial value extraction.

### IADB Normalizer

**Fields Mapping:**
- `notice_title` → `title`
- No direct mapping for `description` (possibly extract from PDFs)
- `publication_date` → `publication_date`
- `pue_date` → `deadline_date`
- `country` → `country`
- `url` and `url_pdf` → `document_links`

**Potential Improvements:**
- Extract descriptions from PDF content.
- Add extraction of financial information.
- Derive procurement methods from notice titles or PDF content.

### AFDB Normalizer

**Fields Mapping:**
- `title` → `title`
- `description` → `description`
- `publication_date` → `publication_date`
- `closing_date` → `deadline_date`
- `country` → `country`
- `sector` → `sector`
- `project_name` → `project_name`
- `document_links` → `document_links`

**Potential Improvements:**
- Extract city information.
- Extract organization names and buyer information.
- Improve financial information extraction.

### AIIB Normalizer

**Fields Mapping:**
- Uses `project_notice` field as both title and description.
- `date` → `publication_date`
- `member` → `country`
- `sector` → `sector`
- `type` → `tender_type`

**Potential Improvements:**
- Extract descriptions from PDF content.
- Add dedicated deadline date extraction.
- Extract organization names from content.

### SAM.gov Normalizer

**Fields Mapping:**
- `opportunity_title` → `title`
- `description` → `description`
- `publish_date` → `publication_date`
- `response_date` → `deadline_date`
- `opportunity_status` → `status`
- `organisation_id` or `org_key` → `organization_id`
- Extracts location from `place_of_performance`

**Potential Improvements:**
- Better extraction of procurement methods.
- Improved organization name extraction.
- Financial information extraction from descriptions.

## Common Improvement Areas

1. **Consistent Error Handling:** Implement consistent error handling across all normalizers with proper attribute checking.

2. **Financial Information Extraction:** Improve extraction of financial values and currencies from textual descriptions.

3. **Organization Names:** Enhance extraction of organization names and buyer information from various fields.

4. **Document Links:** Standardize document link normalization across all sources.

5. **Status Determination:** Create a consistent approach to determine tender status based on dates.

6. **Procurement Methods:** Improve extraction and standardization of procurement methods.

7. **Date Parsing:** Standardize date parsing across different formats and handle edge cases.

8. **Language Detection:** Improve language detection for better translation.

9. **Location Information:** Enhance extraction of country and city information from addresses and descriptions.

10. **Fallback Mechanisms:** Implement consistent fallback mechanisms when primary fields are missing.

## Conclusion

The recent fixes to the TED EU and AFD normalizers have addressed critical issues that were causing attribute errors. The normalizers now correctly use the available fields and include proper attribute checks.

By implementing the suggested improvements, the normalization process can be further enhanced to produce more complete and accurate unified tender data across all sources. 