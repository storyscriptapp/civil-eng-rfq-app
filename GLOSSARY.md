# Glossary of Terms

## Project-Specific Terms

### RFQ / RFP
- **RFQ** = Request for Qualifications
- **RFP** = Request for Proposal
- Used interchangeably in this codebase (legacy naming)
- Refers to government solicitations for civil engineering projects

### Job vs RFQ
- **Job**: Internal term for a tracked RFQ opportunity
- **RFQ**: The actual solicitation document from a municipality
- In code, these are often the same object

## Database & Tracking

### `job_id`
- **Format**: `RFQ-{12-character-hash}`
- **Generated from**: SHA256 hash of `organization + rfp_number`
- **Purpose**: Stable, unique identifier that persists across scrapes
- **Example**: `RFQ-5d4a6983d20d`

### `rfp_number`
- The **official solicitation number** from the organization
- **Examples**: 
  - `"RFP-2025-001"` (Gilbert)
  - `"CP1191(PDF, 264KB)"` (Mesa - includes file size)
  - `"RFB-26-111"` (Yuma - Bonfire format)
- **Note**: Mesa includes PDF file info in the number; this is intentional

### `user_status`
- **Values**: `new`, `ignore`, `pursuing`, `completed`
- **Purpose**: Track user's decision about each RFQ
- **Persists**: Across multiple scrapes

### `work_type`
- **Values**: `civil`, `water`, `electrical`, `landscaping`, `maintenance`, `unknown`
- **Auto-detected**: From title keywords
- **Editable**: User can change via UI

### `status` (scrape status)
- **Values**: `active`, `disappeared`
- **Purpose**: Track if RFQ is still visible on the website
- **Auto-updated**: Each scrape

## Scraping Terms

### Organization
- The municipality or government entity posting the RFQ
- **Examples**: "City of Gilbert", "Town of Florence", "Pinal County"

### Bonfire Sites
- RFQ platforms that use bonfirehub.com
- **Different structure**: Status in cell[0], RFP# in cell[1], Title in cell[2]
- **Current Bonfire orgs**: City of Yuma, Pinal County

### Cloudflare Protection
- Bot detection service used by some sites
- **Requires**: `undetected-chromedriver` to bypass
- **Current Cloudflare orgs**: Town of Florence, Town of Queen Creek

### Pagination
- Multiple pages of RFQs on a single website
- **Handled**: Automatically by scraper
- **Safety**: Max 10 pages, duplicate detection via `seen_titles`

### `row_selector`
- CSS selector to find RFQ rows in HTML tables
- **Examples**:
  - `"table tbody tr"` - Standard table rows
  - `".opportunity-row"` - OpenGov class-based

### `cell_count`
- Expected number of table cells per RFQ row
- **Varies by organization**: 2-5 cells
- **Used for**: Validation and parsing logic

## API & UI Terms

### Journal Entry
- User notes attached to a specific job
- **Stored**: In `job_journal` table
- **Includes**: Timestamp, user name, note text
- **Purpose**: Track progress, contacts, decisions

### Scrape History
- Record of when a job was first/last seen
- **Fields**: `first_seen`, `last_seen`
- **Purpose**: Detect new RFQs and track disappeared ones

### Health Monitor
- Tracks scraper performance over time
- **Metrics**: RFQ counts, error rates, strategy success
- **Alerts**: Significant drops in RFQ counts

### Strategy (Fallback)
- Alternative CSS selectors tried when primary fails
- **Auto-repair**: Updates `cities.json` with working selector
- **Purpose**: Resilience when websites change structure

## File Naming Conventions

### Code Files
- `multi_scraper.py` - Main scraping logic
- `job_tracking.py` - Database and job ID management
- `scraper_health.py` - Performance monitoring
- `scraper_strategies.py` - Fallback selector logic
- `api.py` - FastAPI backend
- `App.js` - React main component
- `JobDetails.js` - React job detail page

### Data Files
- `cities.json` - Configuration for each organization
- `rfqs.json` - Latest scraped RFQs (with job IDs and user decisions)
- `rfq_tracking.db` - SQLite database (persistent storage)
- `scraper_history.json` - Historical scrape metrics

## Common Abbreviations

- **RFQ**: Request for Qualifications
- **RFP**: Request for Proposal  
- **CMAR**: Construction Manager at Risk
- **A/E**: Architect/Engineer
- **PM/CM**: Project Management / Construction Management
- **API**: Application Programming Interface
- **UI**: User Interface
- **DB**: Database
- **JSON**: JavaScript Object Notation
- **CSS**: Cascading Style Sheets (for selectors)
- **OCR**: Optical Character Recognition (fallback for failed scrapes)

## Naming Conventions

### Variables
- **Snake_case**: Python variables (`rfp_number`, `user_status`)
- **camelCase**: JavaScript variables (`selectedJobId`, `filteredRfqs`)
- **PascalCase**: React components (`JobDetails`, `App`)

### Functions
- **Descriptive verbs**: `create_driver()`, `generate_job_id()`, `update_user_status()`
- **Prefixes**:
  - `get_` - Retrieve data
  - `update_` - Modify data
  - `create_` - Create new resource
  - `process_` - Transform data

### Database Tables
- **Plural nouns**: `jobs`, `user_decisions`, `job_journal`
- **Lowercase**: All table names are lowercase

