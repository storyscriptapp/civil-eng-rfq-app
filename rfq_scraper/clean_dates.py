import sqlite3
import os
import re
from datetime import datetime
from dateutil import parser

db_path = os.path.join(os.path.dirname(__file__), 'rfq_tracking.db')

def clean_date(date_str, org_name):
    """
    Convert various date formats to standardized: mm/dd/yy hh:mm PM
    Default to 5:00 PM if no time is provided
    """
    if not date_str or date_str.strip() == '':
        return 'N/A'
    
    # Remove extra whitespace and newlines
    date_str = ' '.join(date_str.split())
    
    # Skip if it's obviously not a date (too long, contains address/subscribe, etc.)
    if len(date_str) > 100 or 'Subscribe' in date_str or 'Arizona' in date_str or 'Map' in date_str:
        return 'N/A'
    
    # Skip if it looks like a department name or work type
    departments = ['Municipal Court', 'Transit', 'Community Development', 'Police Department', 
                   'Fire Department', 'Public Works', 'Jobs', 'Parks']
    if date_str in departments:
        return 'N/A'
    
    try:
        # Common patterns to try
        
        # Pattern 1: "Oct 20th 2025, 5:00 PM MST" (Peoria, Scottsdale, Pinal, Yuma, Apache)
        match = re.match(r'(\w+)\s+(\d+)(?:st|nd|rd|th)\s+(\d{4}),?\s+(\d+):(\d+)\s+(AM|PM)', date_str, re.IGNORECASE)
        if match:
            month_str, day, year, hour, minute, ampm = match.groups()
            month_num = datetime.strptime(month_str, '%b').month
            dt = datetime(int(year), month_num, int(day), int(hour), int(minute))
            if ampm.upper() == 'PM' and int(hour) != 12:
                dt = dt.replace(hour=dt.hour + 12)
            elif ampm.upper() == 'AM' and int(hour) == 12:
                dt = dt.replace(hour=0)
            return dt.strftime('%m/%d/%y %I:%M %p')
        
        # Pattern 2: "04/10/2025 3:00 PM" (Gilbert)
        match = re.match(r'(\d{2})/(\d{2})/(\d{4})\s+(\d+):(\d+)\s+(AM|PM)', date_str, re.IGNORECASE)
        if match:
            month, day, year, hour, minute, ampm = match.groups()
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
            if ampm.upper() == 'PM' and int(hour) != 12:
                dt = dt.replace(hour=dt.hour + 12)
            elif ampm.upper() == 'AM' and int(hour) == 12:
                dt = dt.replace(hour=0)
            return dt.strftime('%m/%d/%y %I:%M %p')
        
        # Pattern 3: "February 20, 2025, by 2 p.m." (Mesa)
        match = re.match(r'(\w+)\s+(\d+),?\s+(\d{4}),?\s+by\s+(\d+)\s+([ap]\.?m\.?)', date_str, re.IGNORECASE)
        if match:
            month_str, day, year, hour, ampm = match.groups()
            month_num = datetime.strptime(month_str, '%B').month
            dt = datetime(int(year), month_num, int(day), int(hour), 0)
            if 'p' in ampm.lower() and int(hour) != 12:
                dt = dt.replace(hour=dt.hour + 12)
            elif 'a' in ampm.lower() and int(hour) == 12:
                dt = dt.replace(hour=0)
            return dt.strftime('%m/%d/%y %I:%M %p')
        
        # Pattern 4: "08/22/2025 1:55 PM" (Yuma County)
        match = re.match(r'(\d{2})/(\d{2})/(\d{4})\s+(\d+):(\d+)\s+(AM|PM)', date_str, re.IGNORECASE)
        if match:
            month, day, year, hour, minute, ampm = match.groups()
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
            if ampm.upper() == 'PM' and int(hour) != 12:
                dt = dt.replace(hour=dt.hour + 12)
            elif ampm.upper() == 'AM' and int(hour) == 12:
                dt = dt.replace(hour=0)
            return dt.strftime('%m/%d/%y %I:%M %p')
        
        # Pattern 5: "01-07-25" (Gila - assume mm-dd-yy format, default 5 PM)
        match = re.match(r'(\d{2})-(\d{2})-(\d{2})$', date_str)
        if match:
            month, day, year = match.groups()
            dt = datetime(2000 + int(year), int(month), int(day), 17, 0)  # Default 5 PM
            return dt.strftime('%m/%d/%y %I:%M %p')
        
        # Pattern 6: "Nov 03, 2025 2:00:00 PM MST" (Apache Junction)
        match = re.match(r'(\w+)\s+(\d+),?\s+(\d{4})\s+(\d+):(\d+):(\d+)\s+(AM|PM)', date_str, re.IGNORECASE)
        if match:
            month_str, day, year, hour, minute, second, ampm = match.groups()
            month_num = datetime.strptime(month_str, '%b').month
            dt = datetime(int(year), month_num, int(day), int(hour), int(minute))
            if ampm.upper() == 'PM' and int(hour) != 12:
                dt = dt.replace(hour=dt.hour + 12)
            elif ampm.upper() == 'AM' and int(hour) == 12:
                dt = dt.replace(hour=0)
            return dt.strftime('%m/%d/%y %I:%M %p')
        
        # Last resort: try dateutil parser (flexible but slower)
        # Only use for dates that haven't matched above
        parsed = parser.parse(date_str, fuzzy=True, default=datetime(2025, 1, 1, 17, 0))
        
        # If no time was found in the string, default to 5 PM
        if ':' not in date_str:
            parsed = parsed.replace(hour=17, minute=0)
        
        return parsed.strftime('%m/%d/%y %I:%M %p')
        
    except Exception as e:
        # If all parsing fails, return N/A
        print(f"  ⚠️  Could not parse date for {org_name}: '{date_str[:50]}...' - {e}")
        return 'N/A'


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all jobs with their current dates
    cursor.execute("SELECT job_id, organization, title, due_date FROM jobs")
    jobs = cursor.fetchall()
    
    print(f"\n🧹 CLEANING {len(jobs)} JOB DATES...")
    print("=" * 80)
    
    updated_count = 0
    na_count = 0
    unchanged_count = 0
    
    for job_id, org, title, old_date in jobs:
        new_date = clean_date(old_date, org)
        
        if new_date != old_date:
            cursor.execute("UPDATE jobs SET due_date = ? WHERE job_id = ?", (new_date, job_id))
            updated_count += 1
            if new_date == 'N/A':
                na_count += 1
                print(f"  ℹ️  {org}: Set to N/A")
        else:
            unchanged_count += 1
    
    conn.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ Updated: {updated_count} dates")
    print(f"   - Set to N/A: {na_count}")
    print(f"   - Unchanged: {unchanged_count}")
    print(f"   - Total: {len(jobs)}")
    
    # Show sample of cleaned dates
    print("\n📅 SAMPLE CLEANED DATES:")
    print("=" * 80)
    cursor.execute("""
        SELECT DISTINCT organization, 
               (SELECT due_date FROM jobs j2 WHERE j2.organization = j1.organization LIMIT 1) as sample_date
        FROM jobs j1
        WHERE (SELECT due_date FROM jobs j2 WHERE j2.organization = j1.organization LIMIT 1) != 'N/A'
        ORDER BY organization
        LIMIT 15
    """)
    for org, date in cursor.fetchall():
        print(f"  {org:30s} | {date}")
    
    conn.close()
    print("\n✅ Date cleaning complete!\n")


if __name__ == "__main__":
    main()
