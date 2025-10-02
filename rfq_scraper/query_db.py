import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "rfqs.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Print all RFQs
cursor.execute("SELECT * FROM rfqs")
all_results = cursor.fetchall()
print(f"All RFQs: {len(all_results)}")
for row in all_results:
    print(row)

# Filter by work_type
cursor.execute("SELECT * FROM rfqs WHERE work_type = 'utility/transportation'")
filtered_results = cursor.fetchall()
print(f"Utility/Transportation RFQs: {len(filtered_results)}")
for row in filtered_results[:2]:
    print(row)

# Update completed
cursor.execute("UPDATE rfqs SET completed = 1 WHERE rfp_number = ?", ("CP1254BR01(PDF, 312KB)",))
conn.commit()

conn.close()