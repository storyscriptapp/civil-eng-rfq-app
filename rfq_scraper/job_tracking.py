import hashlib
import json
import sqlite3
from datetime import datetime

class RFQJobTracker:
    """
    Manages unique IDs and tracks user decisions about RFQs
    """
    
    def __init__(self, db_path="rfq_tracking.db"):
        self.db_path = db_path
        self._init_db()
        # Keep a persistent connection for API use
        self.conn = sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """Initialize database with tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Jobs table - permanent record of all RFQs
        # Check if we need to migrate the old table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='jobs'
        """)
        if cursor.fetchone():
            # Table exists, check if it has the old constraint
            cursor.execute("PRAGMA table_info(jobs)")
            # If table exists, we'll handle updates via ON CONFLICT
            pass
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                rfp_number TEXT,
                organization TEXT,
                title TEXT,
                due_date TEXT,
                link TEXT,
                first_seen DATE,
                last_seen DATE,
                status TEXT DEFAULT 'active',
                work_type TEXT,
                user_status TEXT DEFAULT 'new',
                user_notes TEXT,
                UNIQUE(organization, rfp_number)
            )
        """)
        
        # User decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_decisions (
                job_id TEXT,
                decision TEXT,
                decision_date DATE,
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_job_id(self, org, rfp_number, title):
        """
        Generate a unique, stable ID for a job
        Same RFQ always gets same ID, even across scrapes
        Based on org + rfp_number only (not title) to handle title corrections
        """
        # Create hash from org + rfp_number only (more stable when orgs fix typos)
        # This allows titles to be updated without creating duplicate jobs
        unique_string = f"{org}|{rfp_number}".lower().strip()
        hash_obj = hashlib.sha256(unique_string.encode())
        job_id = hash_obj.hexdigest()[:12]  # 12 chars is enough
        return f"RFQ-{job_id}"
    
    def process_scraped_jobs(self, scraped_data):
        """
        Process newly scraped jobs:
        - Assign IDs
        - Merge with existing database
        - Preserve user decisions
        - Mark disappeared jobs
        
        Returns: Enhanced data with job_ids
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        enhanced_data = []
        seen_job_ids = set()
        
        for job in scraped_data:
            # Generate stable ID
            job_id = self.generate_job_id(
                job['organization'],
                job['rfp_number'],
                job['title']
            )
            seen_job_ids.add(job_id)
            
            # Check if job exists
            cursor.execute("""
                SELECT job_id, user_status, user_notes, first_seen
                FROM jobs WHERE job_id = ?
            """, (job_id,))
            existing = cursor.fetchone()
            
            if existing:
                # NEVER overwrite existing job data - user's data is sacred!
                # Only update last_seen to track that we still see this job
                cursor.execute("""
                    UPDATE jobs SET last_seen = ?
                    WHERE job_id = ?
                """, (today, job_id))
                
                # Fetch ALL existing data to return to user
                cursor.execute("""
                    SELECT job_id, rfp_number, organization, title, due_date, 
                           link, first_seen, last_seen, status, work_type,
                           user_status, user_notes
                    FROM jobs WHERE job_id = ?
                """, (job_id,))
                existing_row = cursor.fetchone()
                
                # Use existing data, not scraped data (preserve original)
                job['job_id'] = existing_row[0]
                job['rfp_number'] = existing_row[1]
                job['organization'] = existing_row[2]
                job['title'] = existing_row[3]
                job['due_date'] = existing_row[4]
                job['link'] = existing_row[5]
                job['first_seen'] = existing_row[6]
                job['last_seen'] = today  # Updated
                job['status'] = existing_row[8]
                job['work_type'] = existing_row[9]
                job['user_status'] = existing_row[10]
                job['user_notes'] = existing_row[11]
            else:
                # New job - insert (use INSERT OR IGNORE to handle duplicates in same scrape)
                cursor.execute("""
                    INSERT OR IGNORE INTO jobs (
                        job_id, rfp_number, organization, title,
                        due_date, link, first_seen, last_seen,
                        status, work_type, user_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
                """, (
                    job_id, job['rfp_number'], job['organization'], job['title'],
                    job['due_date'], job['link'], today, today,
                    job['status'], job['work_type']
                ))
                
                job['job_id'] = job_id
                
                # If INSERT was ignored (duplicate), fetch the existing record
                if cursor.rowcount == 0:
                    cursor.execute("""
                        SELECT user_status, user_notes, first_seen
                        FROM jobs WHERE job_id = ?
                    """, (job_id,))
                    existing = cursor.fetchone()
                    if existing:
                        job['user_status'] = existing[0]
                        job['user_notes'] = existing[1]
                        job['first_seen'] = existing[2]
                    else:
                        # Shouldn't happen, but handle it
                        job['user_status'] = 'new'
                        job['user_notes'] = None
                        job['first_seen'] = today
                else:
                    # New insert succeeded
                    job['user_status'] = 'new'
                    job['user_notes'] = None
                    job['first_seen'] = today
            
            enhanced_data.append(job)
        
        # Mark jobs no longer visible as 'disappeared'
        cursor.execute("""
            UPDATE jobs SET status = 'disappeared'
            WHERE last_seen < ? AND status = 'active'
        """, (today,))
        
        conn.commit()
        conn.close()
        
        return enhanced_data
    
    def update_user_decision(self, job_id, decision, notes=None):
        """
        Record user's decision about a job
        
        decision: 'ignore', 'pursuing', 'completed', 'declined'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        # Update job record
        cursor.execute("""
            UPDATE jobs SET user_status = ?, user_notes = ?
            WHERE job_id = ?
        """, (decision, notes, job_id))
        
        # Log the decision
        cursor.execute("""
            INSERT INTO user_decisions (job_id, decision, decision_date, notes)
            VALUES (?, ?, ?, ?)
        """, (job_id, decision, today, notes))
        
        conn.commit()
        conn.close()
    
    def get_jobs_by_status(self, user_status=None):
        """Get jobs filtered by user status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_status:
            cursor.execute("""
                SELECT * FROM jobs WHERE user_status = ?
                ORDER BY last_seen DESC
            """, (user_status,))
        else:
            cursor.execute("""
                SELECT * FROM jobs ORDER BY last_seen DESC
            """)
        
        columns = [desc[0] for desc in cursor.description]
        jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jobs
    
    def get_stats(self):
        """Get summary statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        stats['total_jobs'] = cursor.fetchone()[0]
        
        # By user status
        cursor.execute("""
            SELECT user_status, COUNT(*) 
            FROM jobs 
            GROUP BY user_status
        """)
        stats['by_status'] = dict(cursor.fetchall())
        
        # Active vs disappeared
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM jobs 
            GROUP BY status
        """)
        stats['by_activity'] = dict(cursor.fetchall())
        
        conn.close()
        return stats


# Example usage:
if __name__ == "__main__":
    tracker = RFQJobTracker()
    
    # Simulate scraped data
    test_data = [
        {
            "organization": "City of Gilbert",
            "rfp_number": "RFP-2025-001",
            "title": "Water Treatment Plant Upgrade",
            "due_date": "2025-11-01",
            "link": "https://example.com",
            "status": "Open",
            "work_type": "utility/transportation"
        }
    ]
    
    # Process it
    enhanced = tracker.process_scraped_jobs(test_data)
    print("Enhanced data:", json.dumps(enhanced, indent=2))
    
    # Simulate user ignoring it
    job_id = enhanced[0]['job_id']
    tracker.update_user_decision(job_id, 'ignore', notes='Not our specialty')
    
    # Get stats
    print("\nStats:", json.dumps(tracker.get_stats(), indent=2))

