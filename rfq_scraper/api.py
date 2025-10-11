from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import os
import sys
import subprocess
import json
import re
import shutil
from datetime import date, datetime
from PIL import Image
import pytesseract
import cv2
import numpy as np
from job_tracking import RFQJobTracker
from auth import get_current_username

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from React build
build_path = os.path.join(os.path.dirname(__file__), "..", "rfq-app", "build")
if os.path.exists(build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")

@app.get("/rfqs")
async def get_rfqs():
    # Read from database (source of truth) instead of rfqs.json
    tracker = RFQJobTracker()
    conn = tracker.conn
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT job_id, rfp_number, organization, title, due_date, 
                   link, first_seen, last_seen, status, work_type,
                   user_status, user_notes, job_info, added_by
            FROM jobs
            ORDER BY last_seen DESC, organization, title
        """)
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                "job_id": row[0],
                "rfp_number": row[1],
                "organization": row[2],
                "title": row[3],
                "due_date": row[4],
                "link": row[5],
                "first_seen": row[6],
                "last_seen": row[7],
                "status": row[8],
                "work_type": row[9],
                "user_status": row[10],
                "user_notes": row[11],
                "job_info": row[12] if len(row) > 12 else "",
                "added_by": row[13] if len(row) > 13 else "scraped"
            })
        
        return jobs
    except Exception as e:
        print(f"Error reading from database: {e}")
        return []

@app.get("/health")
async def get_health():
    """Get scraper health monitoring data"""
    health_path = os.path.join(os.path.dirname(__file__), "scraper_health.json")
    try:
        with open(health_path, 'r') as f:
            health_data = json.load(f)
        return health_data
    except FileNotFoundError:
        return {
            "error": "No health data available - scraper has not run yet",
            "alerts": [],
            "cities": {}
        }
    except json.JSONDecodeError:
        return {
            "error": "Health data file is corrupted",
            "alerts": [],
            "cities": {}
        }

@app.get("/verify")
async def verify_auth(username: str = Depends(get_current_username)):
    """Verify authentication credentials"""
    return {"authenticated": True, "username": username}

@app.post("/run_scraper")
async def run_scraper(data: dict = None, username: str = Depends(get_current_username)):
    """Run scraper for all cities or selected cities (requires authentication)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "multi_scraper.py")
    
    # Use the same Python interpreter that's running the API
    python_exe = sys.executable
    
    if data and data.get("cities"):
        # Run scraper for selected cities
        cities_str = ",".join(data["cities"])
        if os.name == 'nt':
            # Windows: create batch file that keeps window open on error
            batch_content = f'@echo off\ncd /d "{script_dir}"\n"{python_exe}" multi_scraper.py --cities "{cities_str}"\necho.\necho Scraper finished. Press any key to close...\npause > nul'
            batch_path = os.path.join(script_dir, "run_scraper_temp.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", batch_path],
                cwd=script_dir
            )
        else:
            subprocess.Popen(
                [python_exe, script_path, "--cities", cities_str],
                cwd=script_dir
            )
        return {"status": "Scraper started for selected cities", "cities": data["cities"]}
    else:
        # Run scraper for all cities
        if os.name == 'nt':
            batch_content = f'@echo off\ncd /d "{script_dir}"\n"{python_exe}" multi_scraper.py\necho.\necho Scraper finished. Press any key to close...\npause > nul'
            batch_path = os.path.join(script_dir, "run_scraper_temp.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", batch_path],
                cwd=script_dir
            )
        else:
            subprocess.Popen(
                [python_exe, script_path],
                cwd=script_dir
            )
        return {"status": "Scraper started for all cities"}

@app.post("/save_cities")
async def save_cities(cities: list):
    with open(os.path.join(os.path.dirname(__file__), "cities.json"), "w") as f:
        json.dump(cities, f, indent=4)
    return {"status": "Cities saved"}

@app.post("/update_job_status")
async def update_job_status(data: dict, username: str = Depends(get_current_username)):
    job_id = data.get("job_id")
    status = data.get("status")
    notes = data.get("notes")
    
    if not job_id or not status:
        return {"error": "Missing job_id or status"}
    
    # Update in tracking database
    tracker = RFQJobTracker()
    tracker.update_user_decision(job_id, status, notes)
    
    # Also update in rfqs.json for immediate UI response
    rfqs_path = os.path.join(os.path.dirname(__file__), "rfqs.json")
    try:
        with open(rfqs_path, 'r') as f:
            rfqs = json.load(f)
        
        # Update the specific job
        for rfq in rfqs:
            if rfq.get('job_id') == job_id:
                rfq['user_status'] = status
                if notes:
                    rfq['user_notes'] = notes
                break
        
        # Save back to file
        with open(rfqs_path, 'w') as f:
            json.dump(rfqs, f, indent=4)
        
        return {"status": "Job status updated", "job_id": job_id, "new_status": status}
    except Exception as e:
        return {"error": str(e)}

@app.post("/update_work_type")
async def update_work_type(data: dict, username: str = Depends(get_current_username)):
    job_id = data.get("job_id")
    work_type = data.get("work_type")
    
    if not job_id or not work_type:
        return {"error": "Missing job_id or work_type"}
    
    # Update in database
    tracker = RFQJobTracker()
    conn = sqlite3.connect(tracker.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE jobs SET work_type = ? WHERE job_id = ?
        """, (work_type, job_id))
        
        conn.commit()
        conn.close()
        
        return {"status": "Work type updated", "job_id": job_id, "work_type": work_type}
    except Exception as e:
        conn.close()
        return {"error": str(e)}

@app.get("/job_details/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed information about a specific job including scrape history and journal entries"""
    tracker = RFQJobTracker()
    # Open a fresh connection to see latest database changes
    conn = sqlite3.connect(tracker.db_path)
    cursor = conn.cursor()
    
    # Get job details
    cursor.execute("""
        SELECT job_id, organization, title, rfp_number, work_type, due_date, 
               link, user_status, user_notes, first_seen, last_seen, job_info, added_by
        FROM jobs
        WHERE job_id = ?
    """, (job_id,))
    
    job = cursor.fetchone()
    if not job:
        conn.close()
        return {"error": "Job not found"}
    
    job_dict = {
        "job_id": job[0],
        "organization": job[1],
        "title": job[2],
        "rfp_number": job[3],
        "work_type": job[4],
        "due_date": job[5],
        "link": job[6],
        "user_status": job[7],
        "user_notes": job[8],
        "first_seen": job[9],
        "last_seen": job[10],
        "job_info": job[11] if len(job) > 11 else "",
        "added_by": job[12] if len(job) > 12 else "scraped"
    }
    
    # Get scrape history (first_seen and last_seen from jobs table)
    cursor.execute("""
        SELECT first_seen, last_seen FROM jobs WHERE job_id = ?
    """, (job_id,))
    
    scrape_result = cursor.fetchone()
    scrape_history = []
    if scrape_result:
        scrape_history = [
            {"scraped_at": scrape_result[0], "label": "First Seen"},
            {"scraped_at": scrape_result[1], "label": "Last Seen"}
        ]
    
    # Get journal entries (stored in a new table we'll create)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            entry_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name TEXT DEFAULT 'User',
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)
    conn.commit()
    
    cursor.execute("""
        SELECT entry_text, created_at, user_name
        FROM job_journal
        WHERE job_id = ?
        ORDER BY created_at DESC
    """, (job_id,))
    
    journal_entries = [
        {"text": row[0], "created_at": row[1], "user_name": row[2]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "job": job_dict,
        "scrape_history": scrape_history,
        "journal_entries": journal_entries
    }

@app.post("/update_job_details")
async def update_job_details(data: dict, username: str = Depends(get_current_username)):
    """Update job title, due date, and other editable fields"""
    job_id = data.get("job_id")
    title = data.get("title")
    due_date = data.get("due_date")
    
    if not job_id:
        return {"error": "Missing job_id"}
    
    # Update in tracking database
    tracker = RFQJobTracker()
    conn = tracker.conn
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if title:
        updates.append("title = ?")
        params.append(title)
        updates.append("title_manually_edited = 1")
    
    if due_date:
        updates.append("due_date = ?")
        params.append(due_date)
        updates.append("due_date_manually_edited = 1")
    
    if updates:
        params.append(job_id)
        query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Also update in rfqs.json
    rfqs_path = os.path.join(os.path.dirname(__file__), "rfqs.json")
    try:
        with open(rfqs_path, 'r') as f:
            rfqs = json.load(f)
        
        for rfq in rfqs:
            if rfq.get('job_id') == job_id:
                if title:
                    rfq['title'] = title
                if due_date:
                    rfq['due_date'] = due_date
                break
        
        with open(rfqs_path, 'w') as f:
            json.dump(rfqs, f, indent=4)
        
        return {"status": "Job updated", "job_id": job_id}
    except Exception as e:
        return {"error": str(e)}

@app.post("/add_journal_entry")
async def add_journal_entry(data: dict):
    """Add a journal entry for a job"""
    job_id = data.get("job_id")
    entry_text = data.get("entry_text")
    user_name = data.get("user_name", "User")
    
    if not job_id or not entry_text:
        return {"error": "Missing job_id or entry_text"}
    
    tracker = RFQJobTracker()
    conn = tracker.conn
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO job_journal (job_id, entry_text, user_name)
        VALUES (?, ?, ?)
    """, (job_id, entry_text, user_name))
    conn.commit()
    
    # Get the created entry
    cursor.execute("""
        SELECT entry_text, created_at, user_name
        FROM job_journal
        WHERE id = last_insert_rowid()
    """)
    entry = cursor.fetchone()
    
    return {
        "status": "Journal entry added",
        "entry": {
            "text": entry[0],
            "created_at": entry[1],
            "user_name": entry[2]
        }
    }

@app.post("/parse_text")
async def parse_text(data: dict):
    """Parse text to extract RFQ information - handles multiple formats"""
    text = data.get("text", "")
    org = data.get("organization", "Unknown")
    url = data.get("url", "")
    
    results = []
    
    # Try multiple patterns for RFP/Project/Code/Solicitation number and title
    rfp_number = ""
    title = ""
    job_info_parts = []
    
    # Pattern 1: Arizona State format with "Code" and "Label"
    code_match = re.search(r'Code\s*\n\s*([^\n]+)', text, re.IGNORECASE)
    label_match = re.search(r'Label\s*\n\s*([^\n]+)', text, re.IGNORECASE)
    if code_match and label_match:
        rfp_number = code_match.group(1).strip()
        title = label_match.group(1).strip()
    else:
        # Try standard patterns with "- Title" format
        patterns = [
            # "Project No.: ABC123 - TITLE"
            r"Project\s+No\.?:\s*([^\s-]+)\s*-\s*(.*?)(?=\n|Pre-Sub|Solicitation|Statement)",
            # "RFP #123 - Title"
            r"(RFP\s*#?[^\s:]+)\s*-\s*(.*?)(?=\n|$)",
            # "RFQ #123 - Title"
            r"(RFQ\s*#?[^\s:]+)\s*-\s*(.*?)(?=\n|$)",
            # "Bid #123 - Title"  
            r"(Bid\s*#?[^\s:]+)\s*-\s*(.*?)(?=\n|$)",
            # "Solicitation #123 - Title"
            r"(Solicitation\s*#?[^\s:]+)\s*-\s*(.*?)(?=\n|$)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            if matches:
                rfp_number, title = matches[0]
                break
        
        # If still no match, try to extract from structured format
        if not rfp_number and not title:
            lines = text.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                # Look for ID patterns
                num_match = re.search(r'((?:Project|RFP|RFQ|Bid|Solicitation|Code)\s*(?:No\.?|#)?:?\s*[\w\.-]+)', first_line, re.IGNORECASE)
                if num_match:
                    rfp_number = num_match.group(1)
                    title = first_line.replace(rfp_number, '').strip(' -:')
                else:
                    title = first_line
                    rfp_number = "N/A"
    
    # Extract all useful info for job_info field
    info_patterns = {
        'Organization': r'Organization\s*\n\s*([^\n]+)',
        'Procurement Officer': r'Procurement Officer\s*\n\s*([^\n]+)',
        'PO Email': r'Procurement Officer Email\s*\n\s*([^\n]+)',
        'PO Phone': r'Procurement Officer Phone\s*\n\s*([^\n]+)',
        'Fiscal Year': r'Fiscal Year\s*\n\s*([^\n]+)',
        'Commodity': r'Commodity\s*\n\s*([^\n]+)',
        'Begin Date': r'Begin Date\s*\n\s*([^\n]+)',
        'Summary': r'Summary\s*\n\s*([^\n]+(?:\n(?!Code|Organization|Label|Fiscal)[^\n]+)*)',
        'Process': r'Process\s*\n\s*([^\n]+(?:\n(?!Code|Organization|Label|Fiscal)[^\n]+)*)',
    }
    
    for key, pattern in info_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                job_info_parts.append(f"{key}: {value}")
    
    # Combine all extra info
    job_info = "\n".join(job_info_parts) if job_info_parts else ""
    
    # Extract due date - look for various formats (including "End Date" for Arizona state)
    due_date = "N/A"
    due_date_patterns = [
        r"End Date\s*\n\s*([^\n]+)",  # Arizona state format
        r"Due Date[:\s]*([^\n]+?)(?:Arizona Time|\n|$)",
        r"Submittal Due Date[:\s]*([^\n]+?)(?:Arizona Time|\n|$)",
        r"(?:Closes?|Closing)[:\s]*([^\n]+?)(?:Arizona Time|\n|$)",
        r"SOQ.*Submittal Due Date[:\s]*([^\n]+?)(?:Arizona Time|\n|$)",
    ]
    
    for pattern in due_date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            due_date = date_match.group(1).strip()
            # Clean up common suffixes
            due_date = re.sub(r'\s*(Arizona Time|MST|AZ|UTC[+-]\d+)', '', due_date).strip()
            # Remove extra whitespace
            due_date = ' '.join(due_date.split())
            break
    
    # Determine work type
    combined_text = (title + " " + text).lower()
    work_type = "unknown"
    if any(word in combined_text for word in ["utility", "irrigation", "sewer", "water", "wastewater", "transportation", "road", "bridge", "hydraulics", "storm drain", "street", "highway"]):
        work_type = "civil"
    elif any(word in combined_text for word in ["landscaping", "maintenance", "cleaning", "janitorial"]):
        work_type = "maintenance"
    elif any(word in combined_text for word in ["construction", "building", "renovation", "demolition"]):
        work_type = "construction"
    
    if rfp_number and title:
        job_data = {
            "organization": org,
            "rfp_number": rfp_number.strip(),
            "title": title.strip(),
            "work_type": work_type,
            "open_date": date.today().strftime("%Y-%m-%d"),
            "due_date": due_date,
            "status": "Open",
            "link": url if url else "",
            "documents": [],
            "job_info": job_info,
            "added_by": "parsed"
        }
        results.append(job_data)
        
        # Save to database directly (not through process_scraped_jobs)
        try:
            from job_tracking import RFQJobTracker
            tracker = RFQJobTracker()
            
            # Generate job ID
            job_id = tracker.generate_job_id(org, rfp_number.strip(), title.strip())
            
            # Insert directly with new fields
            cursor = tracker.conn.cursor()
            today = date.today().strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT OR REPLACE INTO jobs (
                    job_id, rfp_number, organization, title,
                    due_date, link, first_seen, last_seen,
                    status, work_type, user_status, job_info, added_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
            """, (
                job_id, rfp_number.strip(), org, title.strip(),
                due_date, url if url else "", today, today,
                "Open", work_type, job_info, "parsed"
            ))
            
            tracker.conn.commit()
            
            # Add to scrape history
            cursor.execute("""
                INSERT INTO job_scrape_history (job_id, scraped_at, title, due_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, today, title.strip(), due_date, "Open"))
            
            tracker.conn.commit()
            
            print(f"✅ Saved manually parsed job to database: {title[:50]}...")
        except Exception as e:
            print(f"⚠️ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
    
    return {"rfqs": results, "saved_to_db": len(results) > 0}

@app.post("/upload_screenshot")
async def upload_screenshot(file: UploadFile = File(...), organization: str = "Unknown"):
    screenshot_path = os.path.join(os.path.dirname(__file__), f"{organization.lower().replace(' ', '_')}_user_screenshot.png")
    with open(screenshot_path, "wb") as f:
        f.write(await file.read())
    img = cv2.imread(screenshot_path)
    if img is None:
        return {"error": "Failed to load screenshot"}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        table_img = img[y:y+h, x:x+w]
        cv2.imwrite(screenshot_path, table_img)
    text = pytesseract.image_to_string(Image.open(screenshot_path))
    rfq_pattern = re.compile(r"(RFP\s*#[^\s]+)\s*-\s*(.*?)(?=\n|$)", re.MULTILINE)
    matches = rfq_pattern.findall(text)
    results = []
    for rfp_number, title in matches:
        due_date_match = re.search(r"(?:End Date|Due Date)[^\n]*\n([^\n]+)", text, re.IGNORECASE)
        due_date = due_date_match.group(1).strip() if due_date_match else ""
        title_lower = title.lower()
        work_type = "unknown"
        if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
            work_type = "utility/transportation"
        elif any(word in title_lower for word in ["landscaping", "maintenance"]):
            work_type = "maintenance"
        results.append({
            "organization": organization,
            "rfp_number": rfp_number.strip(),
            "title": title.strip(),
            "work_type": work_type,
            "open_date": date.today().strftime("%Y-%m-%d"),
            "due_date": due_date,
            "status": "Open",
            "link": "",
            "documents": []
        })
    return {"rfqs": results}

@app.get("/cities")
async def get_cities():
    """Get all cities/organizations with their configuration and stats"""
    cities_path = os.path.join(os.path.dirname(__file__), "cities.json")
    rfqs_path = os.path.join(os.path.dirname(__file__), "rfqs.json")
    
    try:
        with open(cities_path, 'r') as f:
            cities_config = json.load(f)
        
        # Get job counts per organization
        try:
            with open(rfqs_path, 'r') as f:
                rfqs = json.load(f)
            job_counts = {}
            for rfq in rfqs:
                org = rfq.get('organization', 'Unknown')
                job_counts[org] = job_counts.get(org, 0) + 1
        except:
            job_counts = {}
        
        # Build cities list with placeholder data
        cities = []
        for city in cities_config:
            cities.append({
                "name": city.get("organization", "Unknown"),
                "url": city.get("url", ""),
                "is_active": not city.get("manual", False),
                "job_count": job_counts.get(city.get("organization"), 0),
                # Placeholder fields
                "population_current": None,
                "population_2020": None,
                "contact_name": None,
                "avg_household_income": None,
                "bonds_upcoming": None,
                "bonds_last": None
            })
        
        return cities
    except Exception as e:
        return {"error": str(e)}

@app.get("/city_profile/{city_name}")
async def get_city_profile(city_name: str):
    """Get detailed profile for a specific city/organization"""
    cities_path = os.path.join(os.path.dirname(__file__), "cities.json")
    rfqs_path = os.path.join(os.path.dirname(__file__), "rfqs.json")
    
    try:
        # Find city in config
        with open(cities_path, 'r') as f:
            cities_config = json.load(f)
        
        city_config = None
        for city in cities_config:
            if city.get("organization") == city_name:
                city_config = city
                break
        
        if not city_config:
            return {"error": "City not found"}
        
        # Get job count for this city
        try:
            with open(rfqs_path, 'r') as f:
                rfqs = json.load(f)
            job_count = sum(1 for rfq in rfqs if rfq.get('organization') == city_name)
        except:
            job_count = 0
        
        # Build profile with config data and placeholders
        profile = {
            "name": city_config.get("organization", "Unknown"),
            "url": city_config.get("url", ""),
            "is_active": not city_config.get("manual", False),
            "is_dynamic": city_config.get("is_dynamic", False),
            "uses_cloudflare": city_config.get("uses_cloudflare", False),
            "has_pagination": city_config.get("has_pagination", False),
            "note": city_config.get("note", ""),
            "job_count": job_count,
            # Placeholder fields for demographics
            "population_current": None,
            "population_2020": None,
            "expected_growth": None,
            "avg_household_income": None,
            "drive_time": None,
            # Placeholder fields for contacts
            "contact_name": None,
            "contact_email": None,
            "contact_phone": None,
            # Placeholder fields for bonds
            "bonds_upcoming": None,
            "bonds_last": None,
            "bond_amount": None,
            # Placeholder for notes
            "internal_notes": None,
            # Placeholder for scrape history
            "scrape_history": []
        }
        
        return profile
    except Exception as e:
        return {"error": str(e)}

@app.post("/sync_database")
async def sync_database(
    file: UploadFile = File(...),
    username: str = Depends(get_current_username)
):
    """
    Smart merge: Upload database from dev environment to production.
    - Adds NEW jobs from dev database
    - Updates metadata for existing jobs (title, link, due_date, etc.)
    - PRESERVES all user data (status, notes, journal entries)
    - Creates a backup before making any changes
    """
    temp_db_path = None
    backup_path = None
    
    try:
        prod_db_path = os.path.join(os.path.dirname(__file__), "rfq_tracking.db")
        
        # Verify uploaded file is a SQLite database
        contents = await file.read()
        if not contents.startswith(b'SQLite format 3'):
            return {"success": False, "error": "Invalid file: Not a SQLite database"}
        
        # Save uploaded database to temp file
        temp_db_path = os.path.join(os.path.dirname(__file__), f"temp_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        with open(temp_db_path, 'wb') as f:
            f.write(contents)
        
        # Create backup of production database
        if os.path.exists(prod_db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                os.path.dirname(__file__), 
                f"rfq_tracking_backup_{timestamp}.db"
            )
            shutil.copy2(prod_db_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
        
        # Connect to both databases
        temp_conn = sqlite3.connect(temp_db_path)
        temp_conn.row_factory = sqlite3.Row
        temp_cursor = temp_conn.cursor()
        
        prod_conn = sqlite3.connect(prod_db_path)
        prod_cursor = prod_conn.cursor()
        
        # Get all jobs from uploaded database
        temp_cursor.execute("""
            SELECT job_id, organization, rfp_number, title, link, due_date, 
                   first_seen, last_seen, job_info, added_by
            FROM jobs
        """)
        uploaded_jobs = temp_cursor.fetchall()
        
        jobs_added = 0
        jobs_updated = 0
        title_conflicts = 0
        
        # Process each job from uploaded database
        for job in uploaded_jobs:
            # Check if job exists in production
            prod_cursor.execute("""
                SELECT job_id, user_status, work_type, title_manually_edited, title,
                       due_date_manually_edited, due_date
                FROM jobs WHERE job_id = ?
            """, (job['job_id'],))
            existing_job = prod_cursor.fetchone()
            
            if existing_job is None:
                # NEW JOB - Insert it completely
                prod_cursor.execute("""
                    INSERT INTO jobs (
                        job_id, organization, rfp_number, title, link, due_date,
                        first_seen, last_seen, user_status, work_type, job_info, added_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', 'Unknown', ?, ?)
                """, (
                    job['job_id'], job['organization'], job['rfp_number'], 
                    job['title'], job['link'], job['due_date'],
                    job['first_seen'], job['last_seen'], job['job_info'], job['added_by']
                ))
                jobs_added += 1
            else:
                # EXISTING JOB - Update only metadata, preserve user data
                title_manually_edited = existing_job[3] if len(existing_job) > 3 else 0
                current_title = existing_job[4] if len(existing_job) > 4 else None
                due_date_manually_edited = existing_job[5] if len(existing_job) > 5 else 0
                current_due_date = existing_job[6] if len(existing_job) > 6 else None
                
                # Determine which fields to update
                update_title = not (title_manually_edited and current_title != job['title'])
                update_due_date = not (due_date_manually_edited and current_due_date != job['due_date'])
                
                if title_manually_edited and current_title != job['title']:
                    title_conflicts += 1
                
                # Build dynamic update query based on what should be preserved
                if not update_title and not update_due_date:
                    # Preserve both title and due_date
                    prod_cursor.execute("""
                        UPDATE jobs SET
                            organization = ?,
                            rfp_number = ?,
                            link = ?,
                            last_seen = ?,
                            job_info = ?,
                            added_by = ?
                        WHERE job_id = ?
                    """, (
                        job['organization'], job['rfp_number'],
                        job['link'], job['last_seen'],
                        job['job_info'], job['added_by'], job['job_id']
                    ))
                elif not update_title:
                    # Preserve title, update due_date
                    prod_cursor.execute("""
                        UPDATE jobs SET
                            organization = ?,
                            rfp_number = ?,
                            link = ?,
                            due_date = ?,
                            last_seen = ?,
                            job_info = ?,
                            added_by = ?
                        WHERE job_id = ?
                    """, (
                        job['organization'], job['rfp_number'],
                        job['link'], job['due_date'], job['last_seen'],
                        job['job_info'], job['added_by'], job['job_id']
                    ))
                elif not update_due_date:
                    # Preserve due_date, update title
                    prod_cursor.execute("""
                        UPDATE jobs SET
                            organization = ?,
                            rfp_number = ?,
                            title = ?,
                            link = ?,
                            last_seen = ?,
                            job_info = ?,
                            added_by = ?
                        WHERE job_id = ?
                    """, (
                        job['organization'], job['rfp_number'], job['title'],
                        job['link'], job['last_seen'],
                        job['job_info'], job['added_by'], job['job_id']
                    ))
                else:
                    # Update everything
                    prod_cursor.execute("""
                        UPDATE jobs SET
                            organization = ?,
                            rfp_number = ?,
                            title = ?,
                            link = ?,
                            due_date = ?,
                            last_seen = ?,
                            job_info = ?,
                            added_by = ?
                        WHERE job_id = ?
                    """, (
                        job['organization'], job['rfp_number'], job['title'],
                        job['link'], job['due_date'], job['last_seen'],
                        job['job_info'], job['added_by'], job['job_id']
                    ))
                jobs_updated += 1
        
        # Sync scraper history from uploaded database
        temp_cursor.execute("SELECT * FROM job_scrape_history")
        history_entries = temp_cursor.fetchall()
        
        for entry in history_entries:
            # Insert if doesn't exist (based on job_id + scraped_at)
            prod_cursor.execute("""
                INSERT OR IGNORE INTO job_scrape_history (job_id, scraped_at, rfp_number, title, link, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry['job_id'], entry['scraped_at'], entry['rfp_number'],
                entry['title'], entry['link'], entry['due_date']
            ))
        
        # Commit changes
        prod_conn.commit()
        
        # Get final counts
        prod_cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = prod_cursor.fetchone()[0]
        
        # Close connections
        temp_conn.close()
        prod_conn.close()
        
        # Clean up temp file
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        # Build message
        message = f"Smart sync completed! {jobs_added} new jobs added, {jobs_updated} jobs updated."
        if title_conflicts > 0:
            message += f" {title_conflicts} job(s) kept your custom title (website title was different)."
        
        return {
            "success": True,
            "message": message,
            "jobs_added": jobs_added,
            "jobs_updated": jobs_updated,
            "title_conflicts": title_conflicts,
            "total_jobs": total_jobs,
            "synced_at": datetime.now().isoformat()
        }
            
    except Exception as e:
        # Restore backup if something went wrong
        if backup_path and os.path.exists(backup_path) and os.path.exists(prod_db_path):
            shutil.copy2(backup_path, prod_db_path)
            error_msg = f"Sync failed: {str(e)}. Backup restored."
        else:
            error_msg = f"Sync failed: {str(e)}"
        
        return {"success": False, "error": error_msg}
    
    finally:
        # Clean up temp file if it still exists
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except:
                pass

# Catch-all route to serve React app for any non-API routes
@app.get("/{path:path}")
async def serve_react_app(path: str):
    """
    Serve the React app for all routes that don't match API endpoints.
    This allows React Router to handle client-side routing.
    """
    # Check if the file exists in the build directory
    file_path = os.path.join(build_path, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, serve index.html (for React Router)
    index_path = os.path.join(build_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # If no build exists, return helpful error
    return {
        "error": "Frontend not built",
        "message": "Run 'npm run build' in the rfq-app directory to create production build"
    }