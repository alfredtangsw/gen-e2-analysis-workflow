# Document Corpus

<!--
TEMPLATE: Fill in this file before running any prompts.
This is one of the three static context documents attached to every Copilot Chat session.
-->

## Corpus Overview

**Description**: {What is this document collection? What domain does it cover?}
**Primary use case**: {What questions should users be able to ask against this corpus?}
**Total estimated size**: {e.g., 500 PDFs, ~200MB; or 10,000 web pages}
**Update frequency**: {Static snapshot | Weekly refresh | Real-time streaming}

---

## Document Sources

List every source that will be ingested. Be specific — vague entries cause ingestion failures.

| Source ID | Type | Description | Location / Access Method | Format | Volume | Update Freq |
|-----------|------|-------------|--------------------------|--------|--------|-------------|
| src-001 | {PDF \| HTML \| DOCX \| Markdown \| Database \| API} | {what these docs contain} | {file path / URL / API endpoint} | {format} | {count or size} | {static/daily/etc} |
| src-002 | | | | | | |

---

## Access & Credentials

For each source requiring authentication:

| Source ID | Auth Method | Credential Storage | Notes |
|-----------|------------|-------------------|-------|
| src-001 | {API key \| OAuth \| None} | `.env` var: `{VAR_NAME}` | {rate limits, quotas} |

**Never hardcode credentials.** All secrets must be stored in `.env` and referenced by variable name only.

---

## Document Structure Notes

For each source, describe any structural quirks the chunker needs to handle:

| Source ID | Structure Notes |
|-----------|----------------|
| src-001 | {e.g., "Multi-column PDFs — standard text extraction produces garbled output; use layout-aware parser"} |
| src-001 | {e.g., "HTML pages have nav/footer boilerplate that should be stripped before chunking"} |
| src-001 | {e.g., "DOCX files have section headers in Heading 1/2 styles — preserve hierarchy in metadata"} |

---

## Metadata Fields

List the metadata fields that should be extracted and stored alongside each chunk:

| Field | Type | Source | Description | Required? |
|-------|------|--------|-------------|-----------|
| `source_id` | string | filename / URL | Unique identifier for the source document | Yes |
| `document_type` | string | file extension / manual tag | {PDF, web, policy, report, etc.} | Yes |
| `title` | string | document header / filename | Human-readable document name | Yes |
| `date` | date | document content / file metadata | Publication or last-modified date | Yes |
| `section` | string | heading hierarchy | Section/chapter the chunk came from | Recommended |
| `page_number` | int | PDF metadata | Page number (PDF sources only) | If applicable |
| `author` | string | document metadata | Author(s) | Optional |
| `{custom_field}` | {type} | {source} | {description} | {Y/N} |

---

## Known Data Quality Issues

Document any known issues so agents can handle them explicitly rather than silently:

- {e.g., "src-001 PDFs from 2018 are scanned images — require OCR before text extraction"}
- {e.g., "src-003 API returns HTML entities in text fields — must be decoded"}
- {e.g., "~5% of documents have no date metadata — fall back to file modification date"}
- {e.g., "src-002 contains duplicate documents with different filenames — deduplicate on content hash"}

---

## Exclusions

Documents or content that should NOT be indexed:

- {e.g., "Appendices and bibliography sections"}
- {e.g., "Documents marked DRAFT or SUPERSEDED"}
- {e.g., "Pages with less than 100 words of content after cleaning"}
- {e.g., "Documents created before {date} — out of scope for this use case"}

---

## Corpus Size Estimates

These estimates help the embedding agent choose the right batch size and the indexer choose storage:

| Metric | Estimate |
|--------|---------|
| Total documents | {N} |
| Estimated total tokens (pre-chunking) | {N} |
| Expected chunks (at ~{chunk_size} tokens) | {N} |
| Expected index size | {N MB} |
