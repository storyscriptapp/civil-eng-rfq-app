# RFQ Tracker - Production Update Script
# Run this on your Jellyfin server to deploy updates from Git

$ErrorActionPreference = "Stop"

Write-Host "`n=== RFQ Tracker - Production Update ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host ""
}

# Get script location
$scriptPath = $PSScriptRoot
cd $scriptPath

Write-Host "Current directory: $scriptPath" -ForegroundColor Gray
Write-Host ""

# Step 1: Backup current database
Write-Host "[1/5] Creating backup..." -ForegroundColor Green
try {
    .\backup_database.ps1
    Write-Host "  ✓ Backup created successfully" -ForegroundColor Cyan
} catch {
    Write-Host "  ⚠ Backup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y") {
        Write-Host "Update cancelled." -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 2: Stop API service
Write-Host "[2/5] Stopping API service..." -ForegroundColor Green
try {
    Stop-ScheduledTask -TaskName "RFQTrackerAPI" -ErrorAction SilentlyContinue
    Write-Host "  ✓ API service stopped" -ForegroundColor Cyan
} catch {
    Write-Host "  ⚠ Could not stop service (might not be running)" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Pull latest changes from Git
Write-Host "[3/5] Pulling latest changes from Git..." -ForegroundColor Green
try {
    $gitOutput = git pull
    Write-Host "  $gitOutput" -ForegroundColor Gray
    
    if ($gitOutput -like "*Already up to date*") {
        Write-Host "  ℹ No updates available" -ForegroundColor Yellow
        $continue = Read-Host "Continue with service restart anyway? (Y/n)"
        if ($continue -eq "n") {
            Write-Host "Update cancelled." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "  ✓ Changes pulled successfully" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ✗ Git pull failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Check for dependency updates
Write-Host "[4/5] Checking for dependency updates..." -ForegroundColor Green
if (Test-Path "rfq_scraper\requirements.txt") {
    Write-Host "  Installing Python dependencies..." -ForegroundColor Gray
    cd rfq_scraper
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt --quiet
    deactivate
    cd ..
    Write-Host "  ✓ Dependencies updated" -ForegroundColor Cyan
} else {
    Write-Host "  ℹ No requirements.txt found, skipping" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Start API service
Write-Host "[5/5] Starting API service..." -ForegroundColor Green
try {
    Start-ScheduledTask -TaskName "RFQTrackerAPI" -ErrorAction Stop
    Write-Host "  ✓ API service started" -ForegroundColor Cyan
    
    # Wait a moment and check if it's actually running
    Start-Sleep -Seconds 3
    $taskInfo = Get-ScheduledTask -TaskName "RFQTrackerAPI"
    if ($taskInfo.State -eq "Running") {
        Write-Host "  ✓ Service is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Service may not be running. State: $($taskInfo.State)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Could not start service: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "To start manually, run:" -ForegroundColor Yellow
    Write-Host "  cd rfq_scraper" -ForegroundColor Gray
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "  python -m uvicorn api:app --host 0.0.0.0 --port 8000" -ForegroundColor Gray
}
Write-Host ""

Write-Host "=== Update Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Your RFQ Tracker has been updated!" -ForegroundColor Cyan
Write-Host "Access it at your Cloudflare URL" -ForegroundColor Cyan
Write-Host ""

# Show git log of what changed
Write-Host "Recent changes:" -ForegroundColor White
git log --oneline -5
Write-Host ""

pause

