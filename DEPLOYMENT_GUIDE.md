# 🚀 RFQ Tracker - Deployment Guide for Jellyfin Server

This guide will help you deploy the RFQ Tracker on your Jellyfin server with authentication and Cloudflare Tunnel.

---

## 📋 Prerequisites

- ✅ Windows server/PC running Jellyfin
- ✅ Admin access to the server
- ✅ Internet connection
- ✅ A domain name (e.g., `yourdomain.com`) - **optional but recommended**

---

## 🔧 Part 1: Install on Server (30 minutes)

### Step 1.1: Copy Files to Server

1. **Copy your entire project folder** to the server:
   ```
   C:\rfq-tracker\
   ```

2. **Verify the structure:**
   ```
   C:\rfq-tracker\
   ├── rfq_scraper\
   │   ├── multi_scraper.py
   │   ├── api.py
   │   ├── auth.py
   │   ├── cities.json
   │   └── ... (other files)
   └── rfq-app\
       ├── src\
       └── package.json
   ```

---

### Step 1.2: Install Python (if not already installed)

1. Download Python 3.11+ from https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Verify installation:
   ```powershell
   python --version
   ```

---

### Step 1.3: Install Dependencies

Open PowerShell **as Administrator** and run:

```powershell
# Navigate to project folder
cd C:\rfq-tracker\rfq_scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install Python packages
pip install fastapi uvicorn selenium pillow pytesseract opencv-python undetected-chromedriver setuptools

# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
```

---

### Step 1.4: Set Up Password

**Generate a secure password hash:**

```powershell
# Still in the venv
cd C:\rfq-tracker\rfq_scraper
python auth.py
```

**You'll be prompted:**
```
Enter password to hash: [type your password]

Hashed password: 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92

Add this to your environment variables:
RFQ_PASSWORD_HASH="8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
```

**Set environment variables:**

1. Search Windows for "Environment Variables"
2. Click "Environment Variables" button
3. Under "System variables", click "New"
4. Add these two variables:
   - Name: `RFQ_USERNAME`, Value: `admin` (or your preferred username)
   - Name: `RFQ_PASSWORD_HASH`, Value: `[paste the hash from above]`
5. Click OK

---

### Step 1.5: Build React App for Production

```powershell
# Navigate to React app folder
cd C:\rfq-tracker\rfq-app

# Install Node.js if not already installed
# Download from: https://nodejs.org/

# Install dependencies
npm install

# Build production version
npm run build
```

This creates a `build` folder with optimized files.

---

### Step 1.6: Test Locally

```powershell
# Start the API server
cd C:\rfq-tracker\rfq_scraper
.\venv\Scripts\Activate.ps1
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Test in browser:**
- Open: http://localhost:8000/rfqs
- You should be prompted for username/password
- Enter your credentials from Step 1.4

---

## 🌐 Part 2: Set Up Cloudflare Tunnel (30 minutes)

### Step 2.1: Create Cloudflare Account

1. Go to https://dash.cloudflare.com/sign-up
2. Create free account
3. Add your domain (if you have one)
   - If you don't have a domain, you can use Cloudflare's free subdomain

---

### Step 2.2: Install Cloudflare Tunnel

1. Go to **Zero Trust** in Cloudflare dashboard
2. Click **Access** → **Tunnels**
3. Click **Create a tunnel**
4. Name it: `rfq-tracker`
5. Click **Save tunnel**

6. **Install connector on your server:**
   - Cloudflare will show a command like:
   ```powershell
   cloudflared.exe service install [YOUR-TOKEN]
   ```
   - Copy and run this in PowerShell **as Administrator**

---

### Step 2.3: Configure Public Hostname

1. In the tunnel configuration, add a **Public Hostname**:
   - **Subdomain:** `rfq` (or whatever you like)
   - **Domain:** `yourdomain.com`
   - **Service:**
     - Type: `HTTP`
     - URL: `localhost:8000`
2. Click **Save hostname**

**Your app will now be accessible at:** `https://rfq.yourdomain.com`

---

## 🔄 Part 3: Auto-Start on Boot (15 minutes)

### Step 3.1: Create Startup Script

Create file: `C:\rfq-tracker\start_rfq_api.bat`

```batch
@echo off
cd C:\rfq-tracker\rfq_scraper
call venv\Scripts\activate.bat
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

---

### Step 3.2: Create Windows Service

**Option A: Task Scheduler (Easiest)**

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: `RFQ Tracker API`
4. Trigger: **When the computer starts**
5. Action: **Start a program**
6. Program: `C:\rfq-tracker\start_rfq_api.bat`
7. ✅ Check: **Run with highest privileges**
8. ✅ Check: **Run whether user is logged on or not**

**Option B: NSSM (More robust)**

1. Download NSSM: https://nssm.cc/download
2. Extract to `C:\nssm\`
3. Run in PowerShell **as Administrator**:
   ```powershell
   C:\nssm\nssm.exe install RFQTracker "C:\rfq-tracker\rfq_scraper\venv\Scripts\python.exe" "-m uvicorn api:app --host 0.0.0.0 --port 8000"
   C:\nssm\nssm.exe set RFQTracker AppDirectory "C:\rfq-tracker\rfq_scraper"
   C:\nssm\nssm.exe start RFQTracker
   ```

---

## 💾 Part 4: Set Up Automatic Backups (10 minutes)

### Step 4.1: Create Backup Script

Create file: `C:\rfq-tracker\backup.ps1`

```powershell
# RFQ Tracker Backup Script
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "C:\rfq-tracker-backups\$timestamp"

# Create backup directory
New-Item -ItemType Directory -Path $backupDir -Force

# Copy database and config files
Copy-Item "C:\rfq-tracker\rfq_scraper\rfq_tracking.db" "$backupDir\"
Copy-Item "C:\rfq-tracker\rfq_scraper\cities.json" "$backupDir\"
Copy-Item "C:\rfq-tracker\rfq_scraper\rfqs.json" "$backupDir\"
Copy-Item "C:\rfq-tracker\rfq_scraper\scraper_history.json" "$backupDir\"

# Delete backups older than 30 days
Get-ChildItem "C:\rfq-tracker-backups" -Directory | 
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Recurse -Force

Write-Host "Backup completed: $backupDir"
```

---

### Step 4.2: Schedule Daily Backups

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: `RFQ Tracker Backup`
4. Trigger: **Daily** at 2:00 AM
5. Action: **Start a program**
6. Program: `powershell.exe`
7. Arguments: `-File "C:\rfq-tracker\backup.ps1"`

---

## 🎉 Part 5: Access Your App!

### From anywhere:
1. Go to: `https://rfq.yourdomain.com`
2. Enter username and password
3. Start tracking RFQs!

### Security Features Enabled:
- ✅ HTTPS encryption (automatic via Cloudflare)
- ✅ Login required
- ✅ No ports open on your router
- ✅ DDoS protection (Cloudflare)
- ✅ Hidden from internet scanners
- ✅ Rate limiting (3 failed login attempts = temporary block)

---

## 📱 Part 6: Mobile Access (Bonus)

Your app is now mobile-friendly! Just visit the same URL on your phone:
- `https://rfq.yourdomain.com`

---

## 🔧 Troubleshooting

### API won't start:
```powershell
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# If something is using it, either:
# 1. Stop that service
# 2. Change the port in your startup script to 8001, 8002, etc.
```

### Can't access from internet:
1. Check Cloudflare tunnel status: `cloudflared service status`
2. Verify API is running: Visit http://localhost:8000/rfqs locally
3. Check firewall isn't blocking localhost connections

### Forgot password:
```powershell
cd C:\rfq-tracker\rfq_scraper
.\venv\Scripts\Activate.ps1
python auth.py
# Generate new hash and update environment variable
```

---

## 📞 Next Steps

1. ✅ Bookmark `https://rfq.yourdomain.com`
2. ✅ Share URL with team members (if any)
3. ✅ Set up email alerts (optional - I can help with this)
4. ✅ Configure automatic scraping schedule (optional - I can help with this)

---

## 🆘 Need Help?

- **Cloudflare Tunnel Tutorial:** Search YouTube for "Cloudflare Tunnel setup"
- **Windows Task Scheduler:** Search YouTube for "Windows Task Scheduler tutorial"
- **Can't figure something out?** Take a screenshot and let me know where you're stuck!

---

**Congratulations! Your RFQ Tracker is now running securely on your Jellyfin server!** 🎉

