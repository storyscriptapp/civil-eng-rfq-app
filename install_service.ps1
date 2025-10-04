# RFQ Tracker - Windows Service Installation Script
# This script creates a Windows service that auto-starts the API on boot
# Must be run as Administrator

$ErrorActionPreference = "Stop"

Write-Host "RFQ Tracker - Service Installation" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Get current directory
$scriptPath = $PSScriptRoot
$pythonExe = "$scriptPath\rfq_scraper\venv\Scripts\python.exe"
$apiPath = "$scriptPath\rfq_scraper"

# Check if Python venv exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run the setup first (create venv and install dependencies)" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Creating Windows Task..." -ForegroundColor Green

# Create scheduled task
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "-m uvicorn api:app --host 0.0.0.0 --port 8000" -WorkingDirectory $apiPath
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName "RFQTrackerAPI" -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName "RFQTrackerAPI" -Confirm:$false
}

# Register the task
Register-ScheduledTask -TaskName "RFQTrackerAPI" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "RFQ Tracker API Server - Auto-starts on boot"

Write-Host "`n✓ Service installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The API will now start automatically when Windows boots." -ForegroundColor Cyan
Write-Host ""
Write-Host "To manage the service:" -ForegroundColor White
Write-Host "  • Open Task Scheduler (taskschd.msc)" -ForegroundColor Gray
Write-Host "  • Find 'RFQTrackerAPI' in the task list" -ForegroundColor Gray
Write-Host "  • Right-click to Start/Stop/Disable" -ForegroundColor Gray
Write-Host ""
Write-Host "To start the service now, run:" -ForegroundColor White
Write-Host "  Start-ScheduledTask -TaskName 'RFQTrackerAPI'" -ForegroundColor Yellow
Write-Host ""

pause

