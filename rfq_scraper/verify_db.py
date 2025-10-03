import sqlite3
import json

# Check what's in the database
db = sqlite3.connect('rfq_tracking.db')
cursor = db.cursor()

print("=== DATABASE CONTENTS ===")
rows = cursor.execute('SELECT job_id, organization, rfp_number, title FROM jobs ORDER BY organization, rfp_number').fetchall()
print(f"Total jobs in DB: {len(rows)}\n")

# Group by organization
from collections import defaultdict
by_org = defaultdict(list)
for row in rows:
    by_org[row[1]].append(row)

for org, jobs in sorted(by_org.items()):
    print(f"\n{org}: {len(jobs)} jobs")
    for job in jobs[:3]:  # Show first 3
        print(f"  {job[0]} | {job[2]} | {job[3][:40]}")

# Check JSON
print("\n\n=== JSON CONTENTS ===")
with open('rfqs.json') as f:
    rfqs = json.load(f)

print(f"Total jobs in JSON: {len(rfqs)}\n")

by_org_json = defaultdict(list)
for rfq in rfqs:
    by_org_json[rfq['organization']].append(rfq)

for org, jobs in sorted(by_org_json.items()):
    print(f"\n{org}: {len(jobs)} jobs")
    for job in jobs[:3]:  # Show first 3
        print(f"  {job['job_id']} | {job['rfp_number']} | {job['title'][:40]}")

# Check if any Gilbert job_ids match
print("\n\n=== CHECKING MATCHES ===")
db_ids = set(row[0] for row in rows)
json_ids = set(rfq['job_id'] for rfq in rfqs)

print(f"IDs in both DB and JSON: {len(db_ids & json_ids)}")
print(f"IDs only in DB: {len(db_ids - json_ids)}")
print(f"IDs only in JSON: {len(json_ids - db_ids)}")

if json_ids - db_ids:
    print("\nSample IDs in JSON but NOT in DB:")
    for jid in list(json_ids - db_ids)[:5]:
        rfq = next(r for r in rfqs if r['job_id'] == jid)
        print(f"  {jid} | {rfq['organization']} | {rfq['rfp_number']}")

