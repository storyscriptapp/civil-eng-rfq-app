@echo off
cd /d "C:\Users\erfer\civil-eng-rfq-app\civil-eng-rfq-app\rfq_scraper"
"C:\Users\erfer\civil-eng-rfq-app\civil-eng-rfq-app\venv\Scripts\python.exe" multi_scraper.py --cities "City of Casa Grande,City of Surprise,Coconino County,Graham County,Maricopa County,Pima County"
echo.
echo Scraper finished. Press any key to close...
pause > nul