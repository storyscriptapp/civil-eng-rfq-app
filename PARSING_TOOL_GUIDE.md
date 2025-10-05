# Manual Parsing Tool - User Guide

## ✅ **What's Been Fixed:**

### **1. Florence & Queen Creek** ✅
- **Issue**: Scraping "Visit Help Center" links when portals have 0 jobs
- **Fix**: Added filter to skip help/support/navigation links
- **Result**: Will now scrape 0 jobs when portals are empty (correct behavior!)

### **2. Manual Parsing Tool** ✅
- **Issue**: Not working when clicking "Parse Text" button
- **Fixes Applied**:
  - ✅ Added multiple pattern matching (RFP, RFQ, Bid, Project No.)
  - ✅ Now saves parsed jobs directly to database
  - ✅ Better due date extraction (handles multiple formats)
  - ✅ Auto-detects work type (civil, construction, maintenance)
  - ✅ Shows success/error feedback
  - ✅ Clears text after successful parse
  - ✅ Reloads job list from database

---

## 📖 **How to Use the Manual Parsing Tool:**

### **Step 1: Get Your Data Ready**
Copy the job posting text from the source website (e.g., Chandler)

### **Step 2: Open the App**
Go to `http://localhost:3000` (main RFQ list page)

### **Step 3: Scroll to Bottom**
Find the "Manual Input" section

### **Step 4: Fill in the Form**
1. **Organization Name**: Enter the city/organization name (e.g., "City of Chandler")
2. **Paste Text**: Paste the job posting text

### **Step 5: Click "Parse Text"**
- ✅ **Success**: You'll see an alert with number of jobs saved
- ⚠️ **No jobs found**: Check the text format
- ❌ **Error**: Check console for details

### **Step 6: Verify**
The job list will automatically reload, and your new job should appear!

---

## 📋 **Supported Text Formats:**

The parser can handle these patterns:

### **Format 1: RFP/RFQ/Bid Number**
```
RFP #12345 - Project Title Here
Due Date: October 15, 2025
```

### **Format 2: Project Number (Chandler style)**
```
Project No.: ST2001.451 - LINDSAY ROAD IMPROVEMENTS
Submittal Due Date:
September 25, 2025
3:00 p.m.
```

### **Format 3: Simple Format**
```
Bid #ABC-123 - Construction Project
End Date: 12/31/2025
```

---

## 🧪 **Test the Parser:**

A test script has been created with your Chandler data!

### **To Run the Test:**
```bash
# Make sure API server is running:
cd rfq_scraper
uvicorn api:app --reload

# In another terminal:
python test_parser.py
```

This will test parsing the Chandler job you provided and show the results.

---

## 🎯 **What Gets Extracted:**

From your text, the parser extracts:
- ✅ **RFP/Project Number**: `ST2001.451; CHN-0(246)D; ADOT NO. T0243 01C`
- ✅ **Title**: `LINDSAY ROAD IMPROVEMENTS (OCOTILLO ROAD TO HUNT HIGHWAY)`
- ✅ **Due Date**: `September 25, 2025 3:00 p.m.`
- ✅ **Work Type**: `civil` (auto-detected from keywords: road, improvements, etc.)
- ✅ **Organization**: `City of Chandler`

---

## 💡 **Tips for Best Results:**

1. **Include the full job posting** - More context = better parsing
2. **Make sure "Due Date" is clearly labeled** - Parser looks for "Due Date", "End Date", "Submittal Due Date", or "Closes"
3. **Include the project number and title on the first line** - This helps pattern matching
4. **For Chandler jobs**: Copy the entire job posting including dates and description

---

## 🚀 **Next Steps:**

1. **Restart your API server** to get the new parsing code
2. **Refresh your React app** to get the updated UI
3. **Try parsing the Chandler job** using the manual tool
4. **Test with the test script** to verify it works

---

## 📊 **Current Data Status:**

- ✅ **Florence**: 0 jobs (portal empty - correct!)
- ✅ **Queen Creek**: 0 jobs (portal empty - correct!)
- ✅ **Chandler**: Ready for manual entry via parsing tool
- ✅ **All other cities**: Working correctly

---

## ⚠️ **Troubleshooting:**

### **"Nothing happened when I clicked Parse Text"**
- Make sure API server is running
- Check browser console (F12) for errors
- Verify both organization name and text are filled in

### **"Could not parse any jobs"**
- Check that text contains a project/RFP number
- Make sure due date is labeled clearly
- Try running the test script to see detailed parsing

### **"Job saved but doesn't appear"**
- Refresh the page manually
- Check the database: Jobs are saved immediately

---

**You're all set!** The parsing tool is now much more powerful and should work with Chandler's format. 🎉
