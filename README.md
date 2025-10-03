# Civil Engineering RFQ Tracker

A comprehensive web scraping and tracking system for civil engineering Request for Qualifications (RFQ) and Request for Proposal (RFP) opportunities from multiple Arizona municipalities.

## Features

✨ **Automated Web Scraping**
- Scrapes 7 Arizona municipalities for active RFQs
- Handles dynamic content, iframes, and pagination
- Cloudflare bypass for protected sites
- Multi-strategy fallback when selectors change

🎯 **Intelligent Job Tracking**
- Stable job IDs that persist across scrapes
- Preserves user decisions (pursuing, ignore, completed)
- Detects new and disappeared opportunities
- Auto-categorizes by work type (civil, water, electrical, etc.)

📊 **User-Friendly Dashboard**
- React-based modern UI
- Advanced filtering (organization, work type, status, search)
- Editable work types and user statuses
- Hide ignored jobs option

📝 **Detailed Job Pages**
- Full job information and links
- Scrape history (first seen, last seen)
- User journal for notes and progress tracking
- Editable job titles

🔍 **Health Monitoring**
- Tracks scraper performance over time
- Alerts for significant RFQ count changes
- Success/error rates per organization

## Tech Stack

**Backend:**
- Python 3.13
- Selenium WebDriver (web scraping)
- undetected-chromedriver (Cloudflare bypass)
- FastAPI (REST API)
- SQLite (persistent storage)
- Tesseract OCR (fallback extraction)

**Frontend:**
- React.js
- Modern CSS with filters and dropdowns

## Installation

### Prerequisites

1. **Python 3.13+**
2. **Node.js & npm**
3. **Chrome Browser** (version 140.x currently)
4. **Tesseract OCR** (optional, for OCR fallback)
   - Download: https://github.com/tesseract-ocr/tesseract
   - Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Setup

```bash
# Clone the repository
git clone https://github.com/storyscriptapp/civil-eng-rfq-app.git
cd civil-eng-rfq-app

# Backend setup
cd rfq_scraper
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r ../requirements.txt

# Frontend setup
cd ../rfq-app
npm install
```

## Usage

### Running the Scraper

```bash
cd rfq_scraper
venv\Scripts\activate  # Windows
python multi_scraper.py
```

**Output:**
- `rfqs.json` - Latest scraped RFQs with job tracking
- `rfq_tracking.db` - SQLite database with user decisions and history
- `scraper_history.json` - Performance metrics over time

**Typical runtime:** 3-5 minutes for all 7 cities

### Running the Web App

**Terminal 1 - API Server:**
```bash
cd rfq_scraper
venv\Scripts\activate
uvicorn api:app --reload --port 8000
```

**Terminal 2 - React Frontend:**
```bash
cd rfq-app
npm start
```

**Access:** http://localhost:3000

## Project Structure

```
civil-eng-rfq-app/
├── rfq_scraper/              # Backend Python code
│   ├── multi_scraper.py      # Main scraping logic
│   ├── job_tracking.py       # Job ID and database management
│   ├── scraper_health.py     # Performance monitoring
│   ├── scraper_strategies.py # Fallback selectors
│   ├── api.py                # FastAPI backend
│   ├── cities.json           # Scraper configuration per city
│   ├── rfqs.json             # Latest scraped data (output)
│   ├── rfq_tracking.db       # SQLite database (output)
│   └── venv/                 # Python virtual environment
│
├── rfq-app/                  # Frontend React code
│   ├── src/
│   │   ├── App.js            # Main dashboard component
│   │   ├── JobDetails.js     # Job detail page component
│   │   └── App.css           # Styles
│   ├── public/
│   └── package.json          # Node dependencies
│
├── requirements.txt          # Python dependencies
├── GLOSSARY.md              # Terms and naming conventions
├── ARCHITECTURE.md          # System design documentation
└── README.md                # This file
```

## Monitored Organizations

1. **City of Gilbert** - 30+ active RFQs, pagination support
2. **City of Mesa** - 10+ active RFQs
3. **City of Apache Junction** - Dynamic content, iframe
4. **City of Yuma** - Bonfire platform, pagination
5. **Pinal County** - Bonfire platform
6. **Town of Florence** - Cloudflare protection
7. **Town of Queen Creek** - Cloudflare protection

## Key Features Explained

### Stable Job IDs
Each RFQ gets a unique ID (`RFQ-{hash}`) based on `organization + rfp_number`. This means:
- Same RFQ always has same ID across scrapes
- User decisions (pursuing, ignore) persist
- Can track when jobs first appear and disappear

### Cloudflare Bypass
Florence and Queen Creek use Cloudflare bot protection. The scraper:
- Switches to `undetected-chromedriver` for these sites
- Waits for verification to complete
- Switches back to regular driver after

### Multi-Strategy Fallback
If a website changes structure:
- Tries alternative CSS selectors automatically
- Updates `cities.json` with working selector
- Continues scraping without manual intervention

### Work Type Auto-Detection
Analyzes job titles for keywords:
- "water" → water
- "electrical" → electrical
- "landscaping", "maintenance" → maintenance
- "road", "bridge", "pavement" → civil
- etc.

## Troubleshooting

**Chrome version mismatch:**
- Update Chrome browser or adjust `version_main` in `create_undetected_driver()`

**No RFQs scraped:**
- Check if website changed structure
- Look for fallback strategy messages in output
- Verify internet connection

**Database errors:**
- Delete `rfq_tracking.db` and re-run scraper to rebuild
- Check `migrate_db.py` for schema updates

**API not connecting:**
- Ensure API is running on port 8000
- Check CORS settings in `api.py`
- Verify both API and React are running

## Contributing

When contributing or working with another developer:
1. Read `GLOSSARY.md` for naming conventions
2. Read `ARCHITECTURE.md` for system design
3. Follow existing code patterns
4. Test scraper before committing

## Future Enhancements

- [ ] Email notifications for new RFQs
- [ ] Calendar integration for due dates
- [ ] Document download automation
- [ ] More Arizona municipalities
- [ ] Export to Excel/PDF
- [ ] Team collaboration features

## License

Private project - All rights reserved

## Contact

For questions or issues, contact the project maintainer.
