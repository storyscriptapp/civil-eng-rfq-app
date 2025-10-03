# System Architecture

## Overview

The Civil Engineering RFQ Tracker is a full-stack web application consisting of three main components:

1. **Web Scraper** (Python/Selenium) - Automated data collection
2. **Backend API** (FastAPI/SQLite) - Data storage and business logic
3. **Frontend UI** (React) - User interface and interaction

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         React Frontend (localhost:3000)              │  │
│  │  - Dashboard with filters                            │  │
│  │  - Job details page                                  │  │
│  │  - Status/work type editing                          │  │
│  └────────────┬─────────────────────────────────────────┘  │
└───────────────┼─────────────────────────────────────────────┘
                │ HTTP/JSON
                ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND API                               │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      FastAPI Server (localhost:8000)                 │  │
│  │  - GET /rfqs - List all jobs                         │  │
│  │  - GET /job_details/{id} - Get job details          │  │
│  │  - POST /update_job_status - Update user status     │  │
│  │  - POST /update_work_type - Update work type        │  │
│  │  - POST /add_journal_entry - Add note               │  │
│  └────────────┬─────────────────────────────────────────┘  │
└───────────────┼─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                  DATA LAYER                                 │
│                                                             │
│  ┌─────────────────────┐      ┌──────────────────────┐    │
│  │   rfqs.json         │      │  rfq_tracking.db     │    │
│  │  (Latest scrape)    │      │  (SQLite Database)   │    │
│  │  - 45 jobs          │      │  - jobs table        │    │
│  │  - With job_ids     │      │  - user_decisions    │    │
│  │  - User statuses    │      │  - job_journal       │    │
│  └──────▲──────────────┘      └──────▲───────────────┘    │
│         │                             │                     │
│         │ Written by                  │ Written by          │
│         │                             │                     │
└─────────┼─────────────────────────────┼─────────────────────┘
          │                             │
          │                             │
┌─────────┼─────────────────────────────┼─────────────────────┐
│         │       SCRAPER SYSTEM        │                     │
│         │                             │                     │
│  ┌──────┴──────────────┐   ┌──────────┴──────────────┐    │
│  │  multi_scraper.py   │   │  job_tracking.py        │    │
│  │  - Selenium driver  │   │  - Generate job_ids     │    │
│  │  - Visit websites   │   │  - Merge with DB        │    │
│  │  - Extract data     │   │  - Preserve decisions   │    │
│  └─────────────────────┘   └─────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Supporting Modules                            │  │
│  │  - scraper_health.py    (monitoring)                │  │
│  │  - scraper_strategies.py (fallback selectors)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL WEBSITES                              │
│  - City of Gilbert, Mesa, Apache Junction, Yuma            │
│  - Pinal County, Florence, Queen Creek                      │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Web Scraper (`multi_scraper.py`)

**Purpose:** Automated data collection from municipality websites

**Flow:**
1. Load configuration from `cities.json`
2. For each organization:
   - Create appropriate driver (regular or undetected for Cloudflare)
   - Navigate to URL
   - Wait for dynamic content
   - Handle iframes if needed
   - Extract RFQ data using CSS selectors
   - Handle pagination if present
   - Try fallback strategies if primary fails
3. Pass all scraped data to `job_tracking.py`
4. Write results to `rfqs.json`
5. Generate health report

**Key Technologies:**
- `selenium` - Browser automation
- `undetected-chromedriver` - Cloudflare bypass
- `WebDriverWait` - Handle dynamic content
- `pytesseract` - OCR fallback

**Decision Points:**
- Use undetected driver? → Check `uses_cloudflare` flag
- Skip wait? → Check `skip_wait` flag
- Try pagination? → Check `has_pagination` flag
- Try fallback? → If primary selector finds 0 rows

### 2. Job Tracking System (`job_tracking.py`)

**Purpose:** Generate stable IDs and manage user decisions

**Core Function: `process_scraped_jobs(data)`**

```python
Input:  List of scraped RFQs (dicts)
Output: List of RFQs with job_ids and user statuses

Process:
1. For each RFQ:
   - Generate job_id from SHA256(org + rfp_number)
   - Check if job_id exists in database
   - If exists:
     - Preserve user_status, user_notes
     - Update last_seen date
   - If new:
     - Insert into database
     - Set user_status = 'new'
   - Add job_id to RFQ dict

2. Mark disappeared jobs:
   - Find jobs in DB not in current scrape
   - Set status = 'disappeared'

3. Return enhanced data
```

**Database Schema:**

```sql
-- jobs table (main record)
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    rfp_number TEXT,
    organization TEXT,
    title TEXT,
    due_date TEXT,
    link TEXT,
    first_seen DATE,
    last_seen DATE,
    status TEXT DEFAULT 'active',
    work_type TEXT,
    user_status TEXT DEFAULT 'new',
    user_notes TEXT,
    UNIQUE(organization, rfp_number)
);

-- user_decisions table (historical)
CREATE TABLE user_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    user_status TEXT,
    notes TEXT,
    created_at DATE,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

-- job_journal table (notes/progress)
CREATE TABLE job_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    entry_text TEXT,
    created_at DATETIME,
    user_name TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);
```

### 3. Health Monitoring (`scraper_health.py`)

**Purpose:** Track scraper performance and detect anomalies

**Features:**
- Stores historical scrape results in `scraper_history.json`
- Calculates average RFQ count per organization
- Generates alerts for:
  - Drops > 50% from average
  - Complete failures (0 RFQs when historical avg > 0)
- Tracks which strategy was used (default vs fallback)

**Output:** Health report printed after each scrape

### 4. Fallback Strategies (`scraper_strategies.py`)

**Purpose:** Handle website structure changes automatically

**Strategy List:**
```python
1. Default: Use configured row_selector
2. tbody tr: Standard table rows
3. table tr: All table rows
4. .row: Class-based rows
5. [class*='row']: Any row-like class
6. div[role='row']: Accessibility roles
```

**Auto-Repair:**
If a fallback strategy succeeds:
- Updates `cities.json` with working selector
- Logs the change
- Continues scraping

### 5. Backend API (`api.py`)

**Purpose:** RESTful interface between frontend and data

**Endpoints:**

```python
GET /rfqs
  → Returns all jobs from rfqs.json
  → Filters by user preferences

GET /job_details/{job_id}
  → Queries database for job details
  → Returns job info, scrape history, journal entries

POST /update_job_status
  → Updates user_status in database
  → Updates rfqs.json for immediate UI sync

POST /update_work_type
  → Updates work_type in rfqs.json
  → Persists for future scrapes

POST /update_job_details
  → Updates job title

POST /add_journal_entry
  → Adds timestamped note to job_journal table
  → Includes user name and date/time
```

**Key Design Decision:**
- API opens **fresh DB connections** for each request
- Prevents stale data after scraper runs
- Original persistent connection caused sync issues

### 6. React Frontend

**Component Structure:**

```
App.js (Main Dashboard)
├── filters (state)
│   ├── searchTerm
│   ├── selectedWorkType
│   ├── selectedStatus
│   ├── selectedOrganization
│   └── hideIgnored
├── filteredRfqs (computed)
│   └── applies all filters to rfqs
└── Job Table
    ├── Clickable job_id → opens JobDetails
    └── Inline edit for work_type and user_status

JobDetails.js (Detail Page)
├── Job Information
│   ├── Editable title
│   ├── Organization & RFP number
│   ├── Link to original RFQ
│   └── Work type, status, due date
├── Scrape History
│   ├── First seen date
│   └── Last seen date
└── Journal
    ├── Historical entries (newest first)
    └── Input for new notes
```

**Data Flow:**
```
1. User loads page
   → fetch('/rfqs')
   → Display in table

2. User clicks job_id
   → setState(selectedJobId)
   → fetch(`/job_details/${job_id}`)
   → Render JobDetails component

3. User changes status
   → POST '/update_job_status'
   → Update local state
   → Re-render

4. User adds journal note
   → POST '/add_journal_entry'
   → Fetch updated journal
   → Re-render
```

## Data Flow Summary

```
[Websites] 
    ↓ (scraped by)
[multi_scraper.py]
    ↓ (processes through)
[job_tracking.py]
    ↓ (writes to)
[rfqs.json + rfq_tracking.db]
    ↓ (read by)
[api.py]
    ↓ (served to)
[React Frontend]
    ↓ (user edits)
[api.py]
    ↓ (writes to)
[rfq_tracking.db + rfqs.json]
```

## Key Design Patterns

### 1. Stable ID Generation
**Problem:** Need consistent IDs across scrapes  
**Solution:** Hash of `org + rfp_number` (not title, to handle typo fixes)

### 2. Driver Switching
**Problem:** Cloudflare blocks regular Selenium  
**Solution:** Quit regular driver, create undetected driver, scrape, quit, recreate regular

### 3. Fresh DB Connections
**Problem:** API cached old data after scraper ran  
**Solution:** Open new connection per request instead of persistent

### 4. Duplicate Detection
**Problem:** Pagination can cause duplicate scrapes  
**Solution:** `seen_titles` set within each scrape + `INSERT OR IGNORE`

### 5. Graceful Degradation
**Problem:** Websites change, break scraper  
**Solution:** Try multiple strategies, update config, continue

## Error Handling

**Levels of Fallback:**
1. Primary CSS selector
2. Alternative strategies (6 options)
3. OCR from screenshot
4. Record error, continue to next city

**Never Fails Completely:**
- One city failing doesn't stop others
- Partial data is better than no data
- Errors logged to health report

## Security Considerations

**Current State:**
- No authentication (local use only)
- CORS enabled for localhost:3000
- Database file permissions (OS-level)

**For Production:**
- Add user authentication
- Restrict CORS
- Environment variables for secrets
- HTTPS for API
- Rate limiting

## Performance

**Scraper:**
- ~3-5 minutes for 7 cities
- ~20-40 seconds per city
- Waits for dynamic content (2-8 seconds)
- Cloudflare sites take longer (+10 seconds)

**API:**
- <100ms for /rfqs (reading JSON)
- <50ms for database queries
- No caching (ensures fresh data)

**Frontend:**
- Instant filtering (client-side)
- ~100-200ms for detail page load
- No pagination needed (45 jobs)

## Scalability Considerations

**Current Limits:**
- 7 organizations
- ~45 total jobs
- Single-threaded scraper

**To Scale:**
- Add parallel scraping (ThreadPoolExecutor)
- Cache rfqs.json in API
- Add pagination to frontend
- PostgreSQL instead of SQLite
- Background job queue (Celery)

## Testing Strategy

**Manual Testing:**
1. Run scraper, verify counts
2. Check job details page
3. Edit statuses, verify persistence
4. Add journal notes
5. Restart API, verify data intact

**Automated Testing (Future):**
- Unit tests for job_id generation
- Mock website responses
- API endpoint tests
- Database migration tests

## Deployment

**Current:** Local development only

**Future Options:**
1. **Docker** - Containerize scraper + API
2. **Heroku/Railway** - Deploy API
3. **Vercel/Netlify** - Deploy React frontend
4. **Scheduled Scraping** - Cron job or Task Scheduler
5. **Cloud Database** - Replace SQLite

## Maintenance

**Regular Tasks:**
1. Update Chrome/ChromeDriver versions
2. Check for website structure changes
3. Review health reports for anomalies
4. Clean up old database backups
5. Monitor for new RFQ sources

**When Adding a New City:**
1. Add entry to `cities.json`
2. Test scrape manually
3. Verify `row_selector` and `cell_count`
4. Add Cloudflare/pagination flags if needed
5. Run full scrape to verify

