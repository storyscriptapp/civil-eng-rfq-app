import sqlite3
from job_tracking import RFQJobTracker

# Create a test tracker
tracker = RFQJobTracker()

# Create test data
test_jobs = [
    {
        "organization": "TEST_ORG",
        "rfp_number": "TEST-001",
        "title": "Test Job",
        "due_date": "2025-12-31",
        "link": "http://example.com",
        "status": "active",
        "work_type": "unknown"
    }
]

print("Processing test job...")
result = tracker.process_scraped_jobs(test_jobs)
print(f"Result: {result}")

# Check if it's in the database
conn = sqlite3.connect('rfq_tracking.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM jobs WHERE organization = 'TEST_ORG'")
rows = cursor.fetchall()
print(f"\nFound {len(rows)} TEST_ORG jobs in database")
if rows:
    print("Test job was written successfully!")
else:
    print("ERROR: Test job was NOT written to database!")

# Clean up
cursor.execute("DELETE FROM jobs WHERE organization = 'TEST_ORG'")
conn.commit()
conn.close()

