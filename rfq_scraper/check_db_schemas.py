"""
Compare database schemas to ensure they all match before deployment
"""
import sqlite3
import os

def get_schema(db_path, db_name):
    """Get the schema of all tables in a database"""
    if not os.path.exists(db_path):
        return None, f"❌ {db_name}: Database file not found at {db_path}"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [(row[1], row[2]) for row in cursor.fetchall()]  # (name, type)
            schema[table] = columns
        
        conn.close()
        return schema, None
    except Exception as e:
        return None, f"❌ {db_name}: Error reading database: {str(e)}"

def compare_schemas(schema1, name1, schema2, name2):
    """Compare two schemas and report differences"""
    differences = []
    
    # Check tables
    tables1 = set(schema1.keys())
    tables2 = set(schema2.keys())
    
    missing_in_2 = tables1 - tables2
    missing_in_1 = tables2 - tables1
    
    if missing_in_2:
        differences.append(f"  ⚠️  Tables in {name1} but not in {name2}: {', '.join(missing_in_2)}")
    if missing_in_1:
        differences.append(f"  ⚠️  Tables in {name2} but not in {name1}: {', '.join(missing_in_1)}")
    
    # Check columns in common tables
    for table in tables1 & tables2:
        cols1 = schema1[table]
        cols2 = schema2[table]
        
        col_names1 = [c[0] for c in cols1]
        col_names2 = [c[0] for c in cols2]
        
        missing_cols = set(col_names1) - set(col_names2)
        extra_cols = set(col_names2) - set(col_names1)
        
        if missing_cols:
            differences.append(f"  ⚠️  Table '{table}': Columns in {name1} but not in {name2}: {', '.join(missing_cols)}")
        if extra_cols:
            differences.append(f"  ⚠️  Table '{table}': Columns in {name2} but not in {name1}: {', '.join(extra_cols)}")
    
    return differences

# Database paths
dev_db = os.path.join(os.path.dirname(__file__), 'rfq_tracking.db')
test_prod_db = os.path.join(os.path.dirname(__file__), 'test_production.db')
test_dev_db = os.path.join(os.path.dirname(__file__), 'test_dev.db')

print("=" * 80)
print("DATABASE SCHEMA COMPARISON")
print("=" * 80)

# Get schemas
dev_schema, dev_error = get_schema(dev_db, "Development DB")
test_prod_schema, test_prod_error = get_schema(test_prod_db, "Test Production DB")
test_dev_schema, test_dev_error = get_schema(test_dev_db, "Test Dev DB")

# Print any errors
errors = []
if dev_error:
    errors.append(dev_error)
if test_prod_error:
    errors.append(test_prod_error)
if test_dev_error:
    errors.append(test_dev_error)

if errors:
    print("\n⚠️  ERRORS:\n")
    for error in errors:
        print(error)
    print()

# Show schema for development database (the main one)
if dev_schema:
    print("\n📋 DEVELOPMENT DATABASE SCHEMA:")
    print("-" * 80)
    for table, columns in sorted(dev_schema.items()):
        print(f"\n  Table: {table}")
        for col_name, col_type in columns:
            print(f"    - {col_name} ({col_type})")

# Compare schemas
all_differences = []

if dev_schema and test_prod_schema:
    print("\n\n🔍 COMPARING: Development DB vs Test Production DB")
    print("-" * 80)
    diffs = compare_schemas(dev_schema, "Dev", test_prod_schema, "Test Prod")
    if diffs:
        all_differences.extend(diffs)
        for diff in diffs:
            print(diff)
    else:
        print("  ✅ Schemas match!")

if dev_schema and test_dev_schema:
    print("\n\n🔍 COMPARING: Development DB vs Test Dev DB")
    print("-" * 80)
    diffs = compare_schemas(dev_schema, "Dev", test_dev_schema, "Test Dev")
    if diffs:
        all_differences.extend(diffs)
        for diff in diffs:
            print(diff)
    else:
        print("  ✅ Schemas match!")

# Final summary
print("\n\n" + "=" * 80)
if all_differences:
    print("❌ SCHEMA MISMATCHES FOUND!")
    print("=" * 80)
    print("\n⚠️  Please run the appropriate migration scripts before deploying!")
    print("\nMigration scripts available:")
    print("  - python add_job_info_fields.py")
    print("  - python add_title_flag.py")
    print("  - python add_scrape_history_table.py")
else:
    print("✅ ALL DATABASE SCHEMAS MATCH!")
    print("=" * 80)
    print("\n🚀 Safe to deploy to production!")

print()

