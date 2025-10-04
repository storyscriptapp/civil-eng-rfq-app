# 🔄 Development Workflow - Keep Improving After Deployment!

**YES!** You can keep adding features, fixing bugs, and improving your RFQ Tracker even after it's deployed to your Jellyfin server!

---

## 🎯 The Big Picture

```
┌─────────────────────────────────────────────────────────┐
│  👨‍💻 YOUR LAPTOP (Development)                            │
│  - Make changes                                         │
│  - Test locally                                         │
│  - Commit to Git                                        │
│  - Push to GitHub                                       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ git push
                  ↓
┌─────────────────────────────────────────────────────────┐
│  📦 GITHUB (Code Repository)                            │
│  - Stores all your code                                 │
│  - Version history                                      │
│  - Backup                                               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ git pull
                  ↓
┌─────────────────────────────────────────────────────────┐
│  🏠 JELLYFIN SERVER (Production)                        │
│  - Pull latest code                                     │
│  - Restart API                                          │
│  - Users see updates immediately                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Update Process

### **On Your Laptop:**

```powershell
# 1. Make your changes (code, fix bugs, etc.)

# 2. Test locally
cd rfq_scraper
.\venv\Scripts\Activate.ps1
python -m uvicorn api:app --reload

# 3. Commit and push
git add .
git commit -m "Add feature X"
git push
```

### **On Your Server:**

```powershell
# Just run this one script!
.\update_production.ps1
```

**That's it!** ✨

---

## 📚 Common Development Scenarios

### **Scenario 1: Add a New City**

**On your laptop:**

1. Add city to `rfq_scraper/cities.json`
2. Test: Run scraper for just that city
   ```powershell
   python multi_scraper.py --cities "New City Name"
   ```
3. Commit and push:
   ```powershell
   git add rfq_scraper/cities.json
   git commit -m "Add New City to scraper"
   git push
   ```

**On server:**
```powershell
.\update_production.ps1
```

**Done!** New city is now being scraped in production! 🎉

---

### **Scenario 2: Fix a Bug**

**On your laptop:**

1. Find and fix the bug in your code
2. Test thoroughly locally
3. Commit and push:
   ```powershell
   git add .
   git commit -m "Fix bug in pagination"
   git push
   ```

**On server:**
```powershell
.\update_production.ps1
```

**Done!** Bug is fixed in production! 🐛✨

---

### **Scenario 3: Add New UI Feature**

**On your laptop:**

1. Edit React components in `rfq-app/src/`
2. Test locally:
   ```powershell
   cd rfq-app
   npm start
   ```
3. Build production version:
   ```powershell
   npm run build
   ```
4. Commit and push:
   ```powershell
   git add .
   git commit -m "Add dark mode toggle"
   git push
   ```

**On server:**
```powershell
.\update_production.ps1

# Then rebuild the React app:
cd rfq-app
npm install  # If you added new packages
npm run build
```

**Done!** New UI is live! 🎨

---

### **Scenario 4: Database Changes**

**If you need to add new fields:**

**On your laptop:**

1. Update `job_tracking.py` to add new database columns
2. Create migration script:
   ```python
   # rfq_scraper/migrate_db.py
   import sqlite3
   
   conn = sqlite3.connect("rfq_tracking.db")
   cursor = conn.cursor()
   
   # Add new column
   cursor.execute("""
       ALTER TABLE jobs ADD COLUMN new_field TEXT
   """)
   
   conn.commit()
   conn.close()
   ```
3. Test locally
4. Commit and push

**On server:**
```powershell
# Backup first!
.\backup_database.ps1

# Pull changes
.\update_production.ps1

# Run migration
cd rfq_scraper
.\venv\Scripts\Activate.ps1
python migrate_db.py
```

**Important:** Database changes need extra care! Always backup first! 💾

---

## 🛡️ Safety First - Best Practices

### **1. Always Test Locally**
Never push code directly to production without testing!

```powershell
# On laptop - ALWAYS do this first:
# Test API
cd rfq_scraper
python -m uvicorn api:app --reload

# Test React app
cd rfq-app
npm start

# Test scraper
python multi_scraper.py --cities "Test City"
```

### **2. Use Meaningful Commit Messages**
```powershell
# Good ✅
git commit -m "Add email notifications for new RFQs"
git commit -m "Fix pagination bug in Gilbert scraper"
git commit -m "Update Maricopa County URL"

# Bad ❌
git commit -m "stuff"
git commit -m "changes"
git commit -m "fix"
```

### **3. Backup Before Major Changes**
```powershell
# On server, before updating:
.\backup_database.ps1

# Now safe to proceed!
```

### **4. Keep Dependencies Updated**
```powershell
# On laptop, periodically:
cd rfq_scraper
pip list --outdated

# Update if needed:
pip install --upgrade selenium fastapi uvicorn
```

---

## 🎓 Git Cheat Sheet

### **Basic Commands**

```powershell
# See what changed
git status

# See what you edited
git diff

# Stage all changes
git add .

# Commit with message
git commit -m "Your message here"

# Push to GitHub
git push

# Pull latest from GitHub
git pull

# See recent commits
git log --oneline -10

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

### **Branch Workflow** (Advanced - Optional)

```powershell
# Create a feature branch
git checkout -b feature/new-dashboard

# Make changes, test, commit
git add .
git commit -m "Add dashboard"

# Switch back to main
git checkout main

# Merge your feature
git merge feature/new-dashboard

# Push to GitHub
git push

# Delete branch (cleanup)
git branch -d feature/new-dashboard
```

---

## 📅 Example Development Cycle

### **Week 1: Add Email Notifications**

**Monday (Laptop):**
- Research email libraries
- Add email settings to config
- Write email sending function
- Test locally with your email
- Commit: "Add email notification system"
- Push to GitHub

**Tuesday (Server):**
- Run `update_production.ps1`
- Test email notifications work from production
- Monitor for issues

**Wednesday-Friday:**
- Users use new feature
- You collect feedback

---

### **Week 2: Add 10 More Cities**

**Monday (Laptop):**
- Research city procurement sites
- Add to `cities.json`
- Test each city individually
- Commit: "Add 10 new cities"
- Push to GitHub

**Tuesday (Server):**
- Run `update_production.ps1`
- Run scraper to test new cities
- Check for errors

---

### **Week 3: UI Improvements**

**Throughout week (Laptop):**
- Add dark mode
- Improve mobile layout
- Add export to Excel button
- Test each change
- Commit multiple times
- Push when ready

**Friday (Server):**
- Run `update_production.ps1`
- Rebuild React app
- Show off to colleagues!

---

## 🔍 Troubleshooting Updates

### **"Git pull says 'conflict'"**

```powershell
# On server:
# Option 1: Discard local changes (if you only make changes on laptop)
git reset --hard origin/main
git pull

# Option 2: Stash local changes (if you made changes on server too)
git stash
git pull
git stash pop  # Reapply your changes
```

### **"Service won't start after update"**

```powershell
# Check what's wrong:
cd rfq_scraper
.\venv\Scripts\Activate.ps1
python -m uvicorn api:app --host 0.0.0.0 --port 8000

# Look at error messages
# Fix the issue
# Try again
```

### **"New Python packages not working"**

```powershell
# Reinstall dependencies:
cd rfq_scraper
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --force-reinstall
```

---

## 💡 Pro Tips

### **Tip 1: Keep a TODO List**
```markdown
# TODO.md
- [ ] Add City of Phoenix
- [ ] Fix Maricopa County pagination  
- [x] Add dark mode
- [x] Email notifications
```

### **Tip 2: Version Your Releases**
```markdown
# CHANGELOG.md
## [1.2.0] - 2025-10-15
- Added 10 new cities
- Email notifications
- Dark mode

## [1.1.0] - 2025-10-08
- Fixed pagination bugs
- Performance improvements

## [1.0.0] - 2025-10-04
- Initial deployment
```

### **Tip 3: Document Your Changes**
Add comments in code:
```python
# Added 2025-10-15: Email notification feature
def send_email_notification(rfq):
    # Send email when new RFQ is found
    ...
```

---

## 🎉 The Bottom Line

**You can ABSOLUTELY keep improving your RFQ Tracker!**

The workflow is simple:
1. **Develop** on your laptop
2. **Test** locally
3. **Push** to GitHub
4. **Deploy** to server with one script
5. **Repeat** as often as you want!

**Your data is safe** - the database is preserved across updates.

**Your users stay happy** - minimal downtime during updates.

**You keep learning** - improve your coding skills while making the app better!

---

**Questions about the workflow?** Just ask! 😊

**Ready to add your first feature?** Go for it! 🚀

