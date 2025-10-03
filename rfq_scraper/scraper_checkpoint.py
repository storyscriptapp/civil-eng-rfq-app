"""
Checkpoint system for scraper resumability
Allows scraper to resume from last successful city if it crashes
"""
import json
import os
from datetime import datetime

class ScraperCheckpoint:
    def __init__(self, checkpoint_file="scraper_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
        self.checkpoint = self._load_checkpoint()
    
    def _load_checkpoint(self):
        """Load existing checkpoint or create new one"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {
            "last_completed_city": None,
            "last_completed_index": -1,
            "timestamp": None,
            "status": "not_started"
        }
    
    def should_skip_city(self, city_index, organization):
        """Check if we should skip this city (already completed in this run)"""
        if self.checkpoint["status"] != "in_progress":
            return False
        
        # Skip if we've already completed this city
        return city_index <= self.checkpoint["last_completed_index"]
    
    def mark_city_complete(self, city_index, organization, rfq_count):
        """Mark a city as successfully scraped"""
        self.checkpoint["last_completed_city"] = organization
        self.checkpoint["last_completed_index"] = city_index
        self.checkpoint["timestamp"] = datetime.now().isoformat()
        self.checkpoint["status"] = "in_progress"
        self._save_checkpoint()
        print(f"✓ Checkpoint saved: {organization} ({city_index + 1})")
    
    def mark_complete(self):
        """Mark entire scrape as complete"""
        self.checkpoint["status"] = "completed"
        self.checkpoint["timestamp"] = datetime.now().isoformat()
        self._save_checkpoint()
        print("✓ Scrape completed successfully!")
    
    def reset(self):
        """Reset checkpoint for fresh start"""
        self.checkpoint = {
            "last_completed_city": None,
            "last_completed_index": -1,
            "timestamp": None,
            "status": "not_started"
        }
        self._save_checkpoint()
        print("✓ Checkpoint reset - starting fresh")
    
    def _save_checkpoint(self):
        """Save checkpoint to file"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=4)
    
    def get_resume_info(self):
        """Get information about where to resume from"""
        if self.checkpoint["status"] == "in_progress":
            return {
                "should_resume": True,
                "last_city": self.checkpoint["last_completed_city"],
                "resume_from_index": self.checkpoint["last_completed_index"] + 1,
                "timestamp": self.checkpoint["timestamp"]
            }
        return {
            "should_resume": False,
            "last_city": None,
            "resume_from_index": 0,
            "timestamp": None
        }

