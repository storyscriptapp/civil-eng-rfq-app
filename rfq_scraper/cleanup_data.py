import sqlite3
from datetime import datetime
from dateutil import parser

conn = sqlite3.connect('rfq_tracking.db')
cursor = conn.cursor()

print("="*60)
print("DATA CLEANUP SCRIPT")
print("="*60)

# 1. Add 5 PM to dates without times (Pima County, Maricopa, etc.)
print("\n1. Adding 5 PM to dates without times...")
cursor.execute("""
    SELECT job_id, organization, title, due_date 
    FROM jobs 
    WHERE due_date NOT LIKE '% PM' 
      AND due_date NOT LIKE '% AM' 
      AND due_date != 'N/A'
      AND due_date LIKE '%/%/%'
""")

rows = cursor.fetchall()
updated_count = 0
for row in rows:
    job_id, org, title, due_date = row
    try:
        # Parse the date
        dt = parser.parse(due_date)
        # Set time to 5 PM if no time present
        if dt.hour == 0 and dt.minute == 0:
            dt = dt.replace(hour=17, minute=0)
        # Format as mm/dd/yy hh:mm PM
        new_date = dt.strftime("%m/%d/%y %I:%M %p")
        cursor.execute("UPDATE jobs SET due_date = ? WHERE job_id = ?", (new_date, job_id))
        updated_count += 1
        if updated_count <= 5:
            print(f"  ✓ {org}: {due_date} → {new_date}")
    except Exception as e:
        print(f"  ⚠️ Error updating {org} - {title[:40]}: {e}")

print(f"  Total updated: {updated_count}")

# 2. Delete bad data from Florence, Queen Creek, Chandler, City of Surprise
print("\n2. Deleting bad scraped data...")
bad_orgs = ['Town of Florence', 'Town of Queen Creek', 'City of Chandler', 'City of Surprise']

for org in bad_orgs:
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE organization = ?", (org,))
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("DELETE FROM jobs WHERE organization = ?", (org,))
        print(f"  ✓ Deleted {count} jobs from {org}")

conn.commit()
print("\n✅ Database cleanup complete!")
print("\nYou can now re-scrape these cities with fixed configurations.")
conn.close()
