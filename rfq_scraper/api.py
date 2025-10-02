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
    db_path = os.path.join(os.path.dirname(__file__), "rfqs.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.id, o.name, r.rfp_number, r.title, r.work_type, r.open_date, r.due_date, r.status, r.link, r.scraped_at
    FROM rfqs r JOIN organizations o ON r.organization_id = o.id
    """)
    rfqs = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "organization": r[1], "rfp_number": r[2], "title": r[3], "work_type": r[4], "open_date": r[5], "due_date": r[6], "status": r[7], "link": r[8], "scraped_at": r[9]} for r in rfqs]

@app.post("/run_scraper")
async def run_scraper():
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "multi_scraper.py")])
    return {"status": "Scraper started"}

@app.post("/save_cities")
async def save_cities(cities: list):
    with open(os.path.join(os.path.dirname(__file__), "cities.json"), "w") as f:
        json.dump(cities, f, indent=4)
    return {"status": "Cities saved"}

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