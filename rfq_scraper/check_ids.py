import sqlite3
import json

# Check database
db = sqlite3.connect('rfq_tracking.db').cursor()
yuma_db = db.execute('SELECT job_id, rfp_number, title FROM jobs WHERE organization = ?', ('City of Yuma',)).fetchall()

# Check JSON
with open('rfqs.json') as f:
    rfqs = json.load(f)
yuma_json = [r for r in rfqs if r['organization'] == 'City of Yuma']

print(f'Yuma in DB: {len(yuma_db)}')
for j in yuma_db:
    print(f'  DB: {j[0]} | {j[1]} | {j[2][:40]}')

print(f'\nYuma in JSON: {len(yuma_json)}')
for j in yuma_json:
    print(f'  JSON: {j.get("job_id", "NO ID")} | {j["rfp_number"]} | {j["title"][:40]}')

print("\n" + "="*60)
print("Testing if job_ids match:")
if yuma_json:
    test_id = yuma_json[0].get('job_id')
    print(f"First Yuma JSON job_id: {test_id}")
    
    # Try to find it in DB
    result = db.execute('SELECT * FROM jobs WHERE job_id = ?', (test_id,)).fetchone()
    if result:
        print(f"✅ FOUND in database!")
    else:
        print(f"❌ NOT FOUND in database!")

