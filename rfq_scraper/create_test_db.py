"""
Create a test database with dummy data to safely test the smart merge feature
"""
import sqlite3
import os
from datetime import datetime

# Create test databases
test_prod_db = os.path.join(os.path.dirname(__file__), 'test_production.db')
test_dev_db = os.path.join(os.path.dirname(__file__), 'test_dev.db')

# Remove if they exist
for db in [test_prod_db, test_dev_db]:
    if os.path.exists(db):
        os.remove(db)

# Create "production" database with existing jobs and user data
prod_conn = sqlite3.connect(test_prod_db)
prod_cursor = prod_conn.cursor()

# Create tables (same structure as real db)
prod_cursor.execute('''
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
        job_info TEXT,
        added_by TEXT DEFAULT 'scraped',
        title_manually_edited INTEGER DEFAULT 0
    )
''')

prod_cursor.execute('''
    CREATE TABLE job_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        user_name TEXT,
        entry_text TEXT,
        created_at TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
    )
''')

prod_cursor.execute('''
    CREATE TABLE job_scrape_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        scraped_at TEXT,
        rfp_number TEXT,
        title TEXT,
        link TEXT,
        due_date TEXT
    )
''')

# Add some test jobs with user data
prod_cursor.execute('''
    INSERT INTO jobs (job_id, rfp_number, organization, title, due_date, link, 
                     first_seen, last_seen, status, work_type, user_status, user_notes, job_info, added_by)
    VALUES 
    ('TEST-001', 'RFP-123', 'Test City A', 'Original Job Title', '10/15/25 5:00 PM', 'http://example.com/1',
     '2025-10-01', '2025-10-05', 'active', 'Civil', 'pursuing', NULL, NULL, 'scraped')
''')

prod_cursor.execute('''
    INSERT INTO jobs (job_id, rfp_number, organization, title, due_date, link,
                     first_seen, last_seen, status, work_type, user_status, user_notes, job_info, added_by)
    VALUES 
    ('TEST-002', 'RFP-456', 'Test City B', 'Another Job', '10/20/25 5:00 PM', 'http://example.com/2',
     '2025-10-02', '2025-10-05', 'active', 'Unknown', 'new', NULL, NULL, 'scraped')
''')

# Add journal entry for TEST-001
prod_cursor.execute('''
    INSERT INTO job_journal (job_id, user_name, entry_text, created_at) VALUES 
    ('TEST-001', 'John Doe', 'Called the client, they seem interested!', '2025-10-05 14:30:00')
''')

prod_conn.commit()
prod_conn.close()

print("✅ Created test_production.db with:")
print("   - 2 jobs (TEST-001 has status 'pursuing' and a journal entry)")
print("   - TEST-002 is status 'new'")

# Create "dev" database with new jobs and updates
dev_conn = sqlite3.connect(test_dev_db)
dev_cursor = dev_conn.cursor()

# Create same tables
dev_cursor.execute('''
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
        job_info TEXT,
        added_by TEXT DEFAULT 'scraped',
        title_manually_edited INTEGER DEFAULT 0
    )
''')

dev_cursor.execute('''
    CREATE TABLE job_scrape_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        scraped_at TEXT,
        rfp_number TEXT,
        title TEXT,
        link TEXT,
        due_date TEXT
    )
''')

# Add TEST-001 with UPDATED title (to test metadata update)
dev_cursor.execute('''
    INSERT INTO jobs (job_id, rfp_number, organization, title, due_date, link,
                     first_seen, last_seen, status, work_type, user_status, user_notes, job_info, added_by)
    VALUES 
    ('TEST-001', 'RFP-123', 'Test City A', 'UPDATED Job Title (Changed on Website)', '10/15/25 5:00 PM', 'http://example.com/1',
     '2025-10-01', '2025-10-08', 'active', 'Civil', 'new', NULL, NULL, 'scraped')
''')

# Add TEST-002 (same, no changes)
dev_cursor.execute('''
    INSERT INTO jobs (job_id, rfp_number, organization, title, due_date, link,
                     first_seen, last_seen, status, work_type, user_status, user_notes, job_info, added_by)
    VALUES 
    ('TEST-002', 'RFP-456', 'Test City B', 'Another Job', '10/20/25 5:00 PM', 'http://example.com/2',
     '2025-10-02', '2025-10-08', 'active', 'Unknown', 'new', NULL, NULL, 'scraped')
''')

# Add NEW job TEST-003 (to test adding new jobs)
dev_cursor.execute('''
    INSERT INTO jobs (job_id, rfp_number, organization, title, due_date, link,
                     first_seen, last_seen, status, work_type, user_status, user_notes, job_info, added_by)
    VALUES 
    ('TEST-003', 'RFP-789', 'Test City C', 'Brand New Job from Scraper', '10/25/25 5:00 PM', 'http://example.com/3',
     '2025-10-08', '2025-10-08', 'active', 'Unknown', 'new', NULL, NULL, 'scraped')
''')

dev_conn.commit()
dev_conn.close()

print("\n✅ Created test_dev.db with:")
print("   - TEST-001 with UPDATED title")
print("   - TEST-002 (same)")
print("   - TEST-003 (NEW job)")

print("\n📋 EXPECTED RESULT after smart merge:")
print("   ✅ TEST-001: Title should UPDATE to 'UPDATED Job Title'")
print("   ✅ TEST-001: Status should REMAIN 'pursuing'")
print("   ✅ TEST-001: Journal entry should be PRESERVED")
print("   ✅ TEST-002: Should remain unchanged")
print("   ✅ TEST-003: Should be ADDED as new job")
print("\n🧪 To test:")
print("   1. Copy test_production.db to rfq_tracking.db")
print("   2. Start API server")
print("   3. Use sync button to upload test_dev.db")
print("   4. Check results!")

