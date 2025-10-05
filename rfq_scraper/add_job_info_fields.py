#!/usr/bin/env python3
"""
Add new fields to jobs table:
- job_info: Extra information from manual parsing
- added_by: How the job was added (scraped, manual, parsed)
"""
import sqlite3

conn = sqlite3.connect('rfq_tracking.db')
cursor = conn.cursor()

print("Adding new fields to jobs table...")

# Check if columns already exist
cursor.execute("PRAGMA table_info(jobs)")
columns = [col[1] for col in cursor.fetchall()]

# Add job_info column if it doesn't exist
if 'job_info' not in columns:
    print("  Adding 'job_info' column...")
    cursor.execute("ALTER TABLE jobs ADD COLUMN job_info TEXT")
    print("  ✓ Added 'job_info' column")
else:
    print("  ⏭️  'job_info' column already exists")

# Add added_by column if it doesn't exist
if 'added_by' not in columns:
    print("  Adding 'added_by' column...")
    cursor.execute("ALTER TABLE jobs ADD COLUMN added_by TEXT DEFAULT 'scraped'")
    print("  ✓ Added 'added_by' column")
else:
    print("  ⏭️  'added_by' column already exists")

# Set default values for existing records
cursor.execute("UPDATE jobs SET added_by = 'scraped' WHERE added_by IS NULL")

conn.commit()
conn.close()

print("\n✅ Database migration complete!")
print("New fields:")
print("  - job_info: Stores extra information from manual parsing")
print("  - added_by: Tracks how job was added (scraped, manual, parsed)")

