import sqlite3
import json
import os

# Ensure database path
db_path = os.path.join(os.path.dirname(__file__), "rfqs.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS rfqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization TEXT,
    rfp_number TEXT,
    title TEXT,
    work_type TEXT,
    open_date TEXT,
    due_date TEXT,
    status TEXT,
    link TEXT,
    documents TEXT,
    completed BOOLEAN DEFAULT FALSE,
    hide BOOLEAN DEFAULT FALSE
)
""")

# Clear existing data
cursor.execute("DELETE FROM rfqs")

# Insert data from rfqs.json
with open(os.path.join(os.path.dirname(__file__), "rfqs.json"), "r") as f:
    data = json.load(f)

for item in data:
    cursor.execute("""
    INSERT INTO rfqs (organization, rfp_number, title, work_type, open_date, due_date, status, link, documents)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["organization"],
        item.get("rfp_number", ""),
        item["title"],
        item["work_type"],
        item["open_date"],
        item.get("due_date", ""),
        item["status"],
        item["link"],
        json.dumps(item.get("documents", []))
    ))

conn.commit()
conn.close()
print("Data inserted into rfqs.db")