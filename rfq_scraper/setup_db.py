import sqlite3
import json
import os
from datetime import date  # Fixed import

db_path = os.path.join(os.path.dirname(__file__), "rfqs.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS rfq_tags")
cursor.execute("DROP TABLE IF EXISTS rfq_documents")
cursor.execute("DROP TABLE IF EXISTS rfqs")
cursor.execute("DROP TABLE IF EXISTS organizations")

cursor.execute("""
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE rfqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    rfp_number TEXT,
    title TEXT,
    work_type TEXT,
    open_date TEXT,
    due_date TEXT,
    status TEXT,
    link TEXT,
    scraped_at TEXT,
    completed BOOLEAN DEFAULT FALSE,
    hide BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (organization_id) REFERENCES organizations (id)
)
""")

cursor.execute("""
CREATE TABLE rfq_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfq_id INTEGER,
    label TEXT,
    url TEXT,
    FOREIGN KEY (rfq_id) REFERENCES rfqs (id)
)
""")

cursor.execute("""
CREATE TABLE rfq_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfq_id INTEGER,
    tag TEXT,
    FOREIGN KEY (rfq_id) REFERENCES rfqs (id)
)
""")

with open(os.path.join(os.path.dirname(__file__), "rfqs.json"), "r") as f:
    data = json.load(f)

org_names = set(item["organization"] for item in data)
for org_name in org_names:
    cursor.execute("INSERT OR IGNORE INTO organizations (name) VALUES (?)", (org_name,))

for item in data:
    cursor.execute("SELECT id FROM organizations WHERE name = ?", (item["organization"],))
    org_id = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO rfqs (organization_id, rfp_number, title, work_type, open_date, due_date, status, link, scraped_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        org_id,
        item.get("rfp_number", ""),
        item["title"],
        item["work_type"],
        item["open_date"],
        item.get("due_date", ""),
        item["status"],
        item["link"],
        date.today().strftime("%Y-%m-%d %H:%M:%S")
    ))
    rfq_id = cursor.lastrowid

    documents = item.get("documents", [])
    for doc in documents:
        cursor.execute("INSERT INTO rfq_documents (rfq_id, label, url) VALUES (?, ?, ?)", (rfq_id, doc, ""))

    if item["work_type"] != "unknown":
        cursor.execute("INSERT INTO rfq_tags (rfq_id, tag) VALUES (?, ?)", (rfq_id, item["work_type"]))

conn.commit()
conn.close()
print("Normalized data inserted into rfqs.db")