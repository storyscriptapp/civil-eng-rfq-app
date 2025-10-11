"""
Add title_manually_edited flag to track when users customize job titles
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'rfq_tracking.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(jobs)")
columns = [col[1] for col in cursor.fetchall()]

if 'title_manually_edited' not in columns:
    print("Adding 'title_manually_edited' column...")
    cursor.execute("ALTER TABLE jobs ADD COLUMN title_manually_edited INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Column added successfully!")
else:
    print("ℹ️  Column 'title_manually_edited' already exists.")

conn.close()
print("\n✅ Migration complete!")

