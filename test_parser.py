#!/usr/bin/env python3
"""
Test the manual parsing tool with Chandler data
"""
import requests
import json

# Sample Chandler job data
chandler_text = """Project No.: ST2001.451; CHN-0(246)D; ADOT NO. T0243 01C - LINDSAY ROAD IMPROVEMENTS (OCOTILLO ROAD TO HUNT HIGHWAY)
Pre-Submittal Conference:
N/A	THERE WILL BE NO PRE-SUBMITTAL CONFERENCE
Solicitation Questions Due Date:
September 10, 2025
5:00 p.m.
Arizona Time	All solicitation questions must be emailed to SOQ Questions with the subject line of "City Project No.: ST2001.451; CHN-0(246)D; ADOT No. T0243 01CLindsay Road Improvements (Ocotillo Road to Hunt Highway) RFQ".   Questions received after the due date and time will NOT be considered.
Statement of Qualifications (SOQ) Submittal Due Date:
September 25, 2025
3:00 p.m.
Arizona Time	
SOQ pdf must be emailed to SOQ Submittals.  SOQ's received after the due date and time will NOT be considered.  All SOQs must be emailed as a pdf attachment.  Any SOQ submitted as a link will not be considered.

Project Reference Forms (PRF) must be emailed, by the evaluator, to Project Reference  PRF's received after the due date and time will NOT be considered.

https://project.reference@chandleraz.gov 

Interview Date:
N/A	THERE WILL BE NO INTERVIEWS
Addendum No. 1 issued 9/17/25 - available on the Arizona Procurement Portal

Project Description:

This project will improve Lindsay Road from Ocotillo Road to Hunt Highway including widening to four traffic lanes, ADA upgrades, bike lanes, sidewalk, curb and gutter, street lighting, traffic signals, storm drainage, raised landscape median, wet and dry utilities, irrigation systems, site walls and other improvements.  This is a federally funded project, using FHWA funds.  The estimated construction cost for this project ranges from $30 to $32 Million.    

Scope of Work:

Provide all Construction Management services for the project in accordance with the engineering design and City standards.
"""

print("="*60)
print("TESTING MANUAL PARSING TOOL")
print("="*60)

# Test the parse_text API endpoint
url = "http://localhost:8000/parse_text"
payload = {
    "text": chandler_text,
    "organization": "City of Chandler"
}

print("\nSending request to API...")
print(f"Organization: {payload['organization']}")
print(f"Text length: {len(payload['text'])} characters")

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    print("\n" + "="*60)
    print("PARSE RESULT:")
    print("="*60)
    
    if result.get('rfqs'):
        print(f"\n✅ Successfully parsed {len(result['rfqs'])} job(s)!")
        print(f"✅ Saved to database: {result.get('saved_to_db', False)}")
        
        for i, rfq in enumerate(result['rfqs'], 1):
            print(f"\n--- Job {i} ---")
            print(f"Organization: {rfq['organization']}")
            print(f"RFP Number: {rfq['rfp_number']}")
            print(f"Title: {rfq['title']}")
            print(f"Work Type: {rfq['work_type']}")
            print(f"Due Date: {rfq['due_date']}")
            print(f"Status: {rfq['status']}")
    else:
        print("\n❌ No jobs parsed")
        print("Response:", json.dumps(result, indent=2))
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to API server")
    print("Make sure the FastAPI server is running:")
    print("  cd rfq_scraper")
    print("  uvicorn api:app --reload")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

