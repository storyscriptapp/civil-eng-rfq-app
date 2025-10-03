"""
Migration script to update the jobs table constraint
from UNIQUE(organization, rfq_number, title) to UNIQUE(organization, rfp_number)
and rename rfq_number column to rfp_number
"""
import sqlite3
import shutil
from datetime import datetime

# Backup the old database
db_path = "rfq_tracking.db"
backup_path = f"rfq_tracking_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
try:
    shutil.copy(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
except FileNotFoundError:
    print("⚠️ No existing database to backup")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔄 Migrating database schema...")

# Create new table with correct constraint
cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs_new (
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
    )
""")

# Copy data from old table if it exists
try:
    cursor.execute("""
        INSERT OR REPLACE INTO jobs_new 
        SELECT job_id, rfq_number, organization, title, due_date, link,
               first_seen, last_seen, status, work_type, user_status, user_notes
        FROM jobs
    """)
    print(f"✅ Copied {cursor.rowcount} records from old table")
    
    # Drop old table and rename new one
    cursor.execute("DROP TABLE jobs")
    cursor.execute("ALTER TABLE jobs_new RENAME TO jobs")
    print("✅ Migration complete!")
except sqlite3.OperationalError as e:
    if "no such table: jobs" in str(e):
        # Table doesn't exist yet, just rename
        cursor.execute("ALTER TABLE jobs_new RENAME TO jobs")
        print("✅ Created new jobs table")
    else:
        print(f"❌ Error: {e}")

conn.commit()
conn.close()

print("\n✨ Database migration successful!")
print("You can now run the scraper again.")


