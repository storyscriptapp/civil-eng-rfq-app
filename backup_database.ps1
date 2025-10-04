# RFQ Tracker - Database Backup Script
# Run this script to create a timestamped backup of your database and config files

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups\$timestamp"
$sourceDir = "rfq_scraper"

Write-Host "Creating backup..." -ForegroundColor Green

# Create backup directory
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Files to backup
$filesToBackup = @(
    "$sourceDir\rfq_tracking.db",
    "$sourceDir\cities.json",
    "$sourceDir\rfqs.json",
    "$sourceDir\scraper_history.json",
    "$sourceDir\scraper_checkpoint.json"
)

# Copy files
foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        Copy-Item $file "$backupDir\" -Force
        Write-Host "  ✓ Backed up: $file" -ForegroundColor Cyan
    } else {
        Write-Host "  ⚠ Skipped (not found): $file" -ForegroundColor Yellow
    }
}

# Delete backups older than 30 days
$oldBackups = Get-ChildItem "backups" -Directory | 
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) }

if ($oldBackups) {
    Write-Host "`nCleaning up old backups..." -ForegroundColor Green
    $oldBackups | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        Write-Host "  ✓ Deleted old backup: $($_.Name)" -ForegroundColor Gray
    }
}

Write-Host "`n✓ Backup completed successfully!" -ForegroundColor Green
Write-Host "Location: $backupDir" -ForegroundColor Cyan
Write-Host ""

