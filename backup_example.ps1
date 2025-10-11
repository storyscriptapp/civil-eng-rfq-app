# RFQ Tracker Backup Script
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "C:\rfq-tracker-backups\$timestamp"

# Create backup directory
New-Item -ItemType Directory -Path $backupDir -Force

# Copy database and config files
Copy-Item "C:\rfq-tracker\rfq_scraper\rfq_tracking.db" "$backupDir\"
Copy-Item "C:\rfq-tracker\rfq_scraper\cities.json" "$backupDir\"
Copy-Item "C:\rfq-tracker\rfq_scraper\rfqs.json" "$backupDir\" -ErrorAction SilentlyContinue
Copy-Item "C:\rfq-tracker\rfq_scraper\scraper_history.json" "$backupDir\" -ErrorAction SilentlyContinue

# Delete backups older than 30 days
Get-ChildItem "C:\rfq-tracker-backups" -Directory | 
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Recurse -Force

Write-Host "Backup completed: $backupDir"

