@echo off
cd /d "C:\Users\erfer\civil-eng-rfq-app\civil-eng-rfq-app\rfq_scraper"
"C:\Users\erfer\civil-eng-rfq-app\civil-eng-rfq-app\venv\Scripts\python.exe" multi_scraper.py --cities "Town of Queen Creek,Town of Florence"
echo.
echo Scraper finished. Press any key to close...
pause > nul