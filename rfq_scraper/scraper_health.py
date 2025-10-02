import json
import os
from datetime import datetime
from pathlib import Path

class ScraperHealthMonitor:
    def __init__(self, history_file="scraper_history.json"):
        self.history_file = history_file
        self.history = self._load_history()
        self.current_run = {
            "timestamp": datetime.now().isoformat(),
            "cities": {},
            "total_rfqs": 0,
            "alerts": []
        }
    
    def _load_history(self):
        """Load historical scraping data"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {"runs": []}
    
    def record_city_result(self, org, rfq_count, status="success", error=None, strategy_used=None):
        """Record results for a city"""
        self.current_run["cities"][org] = {
            "rfq_count": rfq_count,
            "status": status,
            "error": error,
            "strategy_used": strategy_used
        }
        self.current_run["total_rfqs"] += rfq_count
        
        # Check for anomalies
        alert = self._check_for_anomalies(org, rfq_count, status)
        if alert:
            self.current_run["alerts"].append(alert)
    
    def _check_for_anomalies(self, org, current_count, status):
        """Detect if results are unusual compared to history"""
        # Get last successful run for this city
        last_count = self._get_last_count(org)
        
        if last_count is None:
            # First time scraping this city
            if status == "success" and current_count > 0:
                return None  # Normal
            elif status != "success":
                return {
                    "city": org,
                    "severity": "warning",
                    "message": f"First scrape failed: {status}"
                }
        else:
            # Compare to historical data
            if status != "success":
                return {
                    "city": org,
                    "severity": "error",
                    "message": f"Scrape failed (previously got {last_count} RFQs)"
                }
            
            # Calculate percent change
            if last_count > 0:
                pct_change = ((current_count - last_count) / last_count) * 100
            else:
                pct_change = 100 if current_count > 0 else 0
            
            # Alert on significant drops
            if pct_change < -50:
                return {
                    "city": org,
                    "severity": "critical",
                    "message": f"RFQ count dropped {abs(pct_change):.1f}% ({last_count} → {current_count})",
                    "pct_change": pct_change
                }
            elif pct_change < -25:
                return {
                    "city": org,
                    "severity": "warning",
                    "message": f"RFQ count dropped {abs(pct_change):.1f}% ({last_count} → {current_count})",
                    "pct_change": pct_change
                }
            elif pct_change > 100:
                return {
                    "city": org,
                    "severity": "info",
                    "message": f"RFQ count increased {pct_change:.1f}% ({last_count} → {current_count})",
                    "pct_change": pct_change
                }
        
        return None
    
    def _get_last_count(self, org):
        """Get the RFQ count from the last successful run for this city"""
        for run in reversed(self.history.get("runs", [])):
            if org in run.get("cities", {}):
                city_data = run["cities"][org]
                if city_data.get("status") == "success":
                    return city_data.get("rfq_count", 0)
        return None
    
    def save_run(self):
        """Save current run to history"""
        self.history.setdefault("runs", []).append(self.current_run)
        
        # Keep only last 30 runs
        if len(self.history["runs"]) > 30:
            self.history["runs"] = self.history["runs"][-30:]
        
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=4)
    
    def generate_report(self):
        """Generate a text report of the current run"""
        report = []
        report.append("=" * 60)
        report.append(f"Scraper Health Report - {self.current_run['timestamp']}")
        report.append("=" * 60)
        report.append(f"\nTotal RFQs collected: {self.current_run['total_rfqs']}")
        report.append(f"Cities scraped: {len(self.current_run['cities'])}")
        
        # Success/failure breakdown
        success = sum(1 for c in self.current_run['cities'].values() if c['status'] == 'success')
        failed = len(self.current_run['cities']) - success
        report.append(f"Success: {success} | Failed: {failed}")
        
        # Alerts
        if self.current_run['alerts']:
            report.append(f"\n⚠️  ALERTS ({len(self.current_run['alerts'])})")
            report.append("-" * 60)
            for alert in self.current_run['alerts']:
                severity_emoji = {
                    "critical": "🚨",
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }
                emoji = severity_emoji.get(alert['severity'], "•")
                report.append(f"{emoji} [{alert['severity'].upper()}] {alert['city']}")
                report.append(f"   {alert['message']}")
        else:
            report.append("\n✅ No alerts - all cities scraped successfully!")
        
        # City-by-city results
        report.append(f"\n📊 CITY RESULTS")
        report.append("-" * 60)
        for org, data in sorted(self.current_run['cities'].items()):
            status_icon = "✅" if data['status'] == 'success' else "❌"
            strategy = f" [{data['strategy_used']}]" if data.get('strategy_used') else ""
            report.append(f"{status_icon} {org}: {data['rfq_count']} RFQs{strategy}")
            if data.get('error'):
                report.append(f"   Error: {data['error']}")
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def send_notification(self, method="console"):
        """Send notification about the run"""
        report = self.generate_report()
        
        if method == "console":
            print("\n" + report)
        elif method == "file":
            with open("scraper_report.txt", "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to scraper_report.txt")
        elif method == "email":
            # TODO: Implement email sending
            print("\n📧 Email notifications not yet implemented")
            print(report)
        
        return report

