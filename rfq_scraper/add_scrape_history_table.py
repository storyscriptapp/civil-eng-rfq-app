"""
Create job_scrape_history table if it doesn't exist
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'rfq_tracking.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_scrape_history'")
table_exists = cursor.fetchone()

if not table_exists:
    print("Creating 'job_scrape_history' table...")
    cursor.execute('''
        CREATE TABLE job_scrape_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            scraped_at TEXT,
            rfp_number TEXT,
            title TEXT,
            link TEXT,
            due_date TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    ''')
    conn.commit()
    print("✅ Table created successfully!")
else:
    print("ℹ️  Table 'job_scrape_history' already exists.")

conn.close()
print("\n✅ Migration complete!")

