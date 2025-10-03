from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import subprocess
import json
import re
from datetime import date
from PIL import Image
import pytesseract
import cv2
import numpy as np
from job_tracking import RFQJobTracker

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/rfqs")
async def get_rfqs():
    # Read from rfqs.json (new format with job tracking)
    rfqs_path = os.path.join(os.path.dirname(__file__), "rfqs.json")
    try:
        with open(rfqs_path, 'r') as f:
            rfqs = json.load(f)
        return rfqs
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

@app.post("/run_scraper")
async def run_scraper():
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "multi_scraper.py")])
    return {"status": "Scraper started"}

@app.post("/save_cities")
async def save_cities(cities: list):
    with open(os.path.join(os.path.dirname(__file__), "cities.json"), "w") as f:
        json.dump(cities, f, indent=4)
    return {"status": "Cities saved"}

@app.post("/update_job_status")
async def update_job_status(data: dict):
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
async def update_work_type(data: dict):
    job_id = data.get("job_id")
    work_type = data.get("work_type")
    
    if not job_id or not work_type:
        return {"error": "Missing job_id or work_type"}
    
    # Update in rfqs.json
    rfqs_path = os.path.join(os.path.dirname(__file__), "rfqs.json")
    try:
        with open(rfqs_path, 'r') as f:
            rfqs = json.load(f)
        
        # Update the specific job
        for rfq in rfqs:
            if rfq.get('job_id') == job_id:
                rfq['work_type'] = work_type
                break
        
        # Save back to file
        with open(rfqs_path, 'w') as f:
            json.dump(rfqs, f, indent=4)
        
        return {"status": "Work type updated", "job_id": job_id, "work_type": work_type}
    except Exception as e:
        return {"error": str(e)}

@app.get("/job_details/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed information about a specific job including scrape history and journal entries"""
    tracker = RFQJobTracker()
    conn = tracker.conn
    cursor = conn.cursor()
    
    # Get job details
    cursor.execute("""
        SELECT job_id, organization, title, rfp_number, work_type, due_date, 
               link, user_status, user_notes, first_seen, last_seen
        FROM rfq_jobs
        WHERE job_id = ?
    """, (job_id,))
    
    job = cursor.fetchone()
    if not job:
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
        "last_seen": job[10]
    }
    
    # Get scrape history
    cursor.execute("""
        SELECT scraped_at FROM rfq_jobs WHERE job_id = ?
        ORDER BY scraped_at DESC
    """, (job_id,))
    
    scrape_history = [{"scraped_at": row[0]} for row in cursor.fetchall()]
    
    # Get journal entries (stored in a new table we'll create)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            entry_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name TEXT DEFAULT 'User',
            FOREIGN KEY (job_id) REFERENCES rfq_jobs(job_id)
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
    
    return {
        "job": job_dict,
        "scrape_history": scrape_history,
        "journal_entries": journal_entries
    }

@app.post("/update_job_details")
async def update_job_details(data: dict):
    """Update job title and other editable fields"""
    job_id = data.get("job_id")
    title = data.get("title")
    
    if not job_id:
        return {"error": "Missing job_id"}
    
    # Update in tracking database
    tracker = RFQJobTracker()
    conn = tracker.conn
    cursor = conn.cursor()
    
    if title:
        cursor.execute("""
            UPDATE rfq_jobs SET title = ? WHERE job_id = ?
        """, (title, job_id))
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
    text = data.get("text", "")
    org = data.get("organization", "Unknown")
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
            "organization": org,
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