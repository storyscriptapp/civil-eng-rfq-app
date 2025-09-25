import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "rfqs.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT * FROM rfqs WHERE work_type = 'utility/transportation'")
results = cursor.fetchall()
print(f"Utility/Transportation RFQs: {len(results)}")
for row in results[:2]:
    print(row)

cursor.execute("UPDATE rfqs SET completed = 1 WHERE rfp_number = ?", ("CP1254BR01",))
conn.commit()

conn.close()