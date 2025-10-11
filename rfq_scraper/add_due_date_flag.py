"""
Add due_date_manually_edited flag to track when users customize due dates
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'rfq_tracking.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(jobs)")
columns = [col[1] for col in cursor.fetchall()]

if 'due_date_manually_edited' not in columns:
    print("Adding 'due_date_manually_edited' column...")
    cursor.execute("ALTER TABLE jobs ADD COLUMN due_date_manually_edited INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Column added successfully!")
else:
    print("ℹ️  Column 'due_date_manually_edited' already exists.")

conn.close()
print("\n✅ Migration complete!")

