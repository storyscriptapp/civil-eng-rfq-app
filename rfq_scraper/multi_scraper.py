from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import date
import time
import os
from PIL import Image
import pytesseract
import cv2
import re
import numpy as np

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load cities
with open("cities.json", "r") as f:
    sites = json.load(f)

options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.headless = False
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

data = []

for site in sites:
    org = site["organization"]
    url = site["url"]
    row_selector = site["row_selector"]
    cell_count = site["cell_count"]
    is_dynamic = site["is_dynamic"]
    manual = site.get("manual", False)

    if manual:
        print(f"Scraping {org} (manual CAPTCHA required)...")
        input(f"Press Enter after resolving CAPTCHA for {org} or skip...")
        time.sleep(2)

    try:
        print(f"Scraping {org}...")
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # Scroll to table
        try:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, row_selector)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
            time.sleep(1)
        except:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        # Handle iframes
        if is_dynamic:
            try:
                iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                driver.switch_to.frame(iframe)
                print(f"Switched to iframe for {org}")
            except:
                print(f"No iframe found for {org}")

        rows = driver.find_elements(By.CSS_SELECTOR, row_selector)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.CSS_SELECTOR, ".opportunity-cell") or row.find_elements(By.TAG_NAME, "div")
            if len(cells) < cell_count:
                continue

            try:
                title_elem = cells[0].find_element(By.TAG_NAME, "a")
                title = title_elem.text.strip().split('\n')[0]
                link = title_elem.get_attribute("href")
                if not link.startswith("http"):
                    link = url.rsplit('/', 1)[0] + '/' + link
            except:
                continue

            if org == "City of Mesa":
                rfp_number = cells[0].text.strip().split('\n')[1].replace("Project No. ", "") if '\n' in cells[0].text else ""
                due_date = cells[1].text.strip()
                documents = cells[2].text.strip().split('\n') if cell_count > 2 else []
            elif org == "City of Gilbert":
                rfp_number = cells[0].text.strip()
                due_date = cells[2].text.strip()
                documents = []
            elif org == "Pinal County":
                if "no open bid postings" in row.text.lower():
                    print(f"No open RFQs for {org}")
                    continue
                rfp_number = cells[0].text.strip()
                due_date = cells[0].text.strip()
                documents = []
            else:
                rfp_number = cells[1].text.strip() if cell_count > 1 else ""
                due_date = cells[2].text.strip() if cell_count > 2 else ""
                documents = []

            status = cells[3].text.strip() if cell_count > 3 else "Open"
            if status != "Open":
                continue

            title_lower = title.lower()
            work_type = "unknown"
            if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
                work_type = "utility/transportation"
            elif any(word in title_lower for word in ["landscaping", "maintenance"]):
                work_type = "maintenance"

            open_date = date.today().strftime("%Y-%m-%d")
            data.append({
                "organization": org,
                "rfp_number": rfp_number,
                "title": title,
                "work_type": work_type,
                "open_date": open_date,
                "due_date": due_date,
                "status": status,
                "link": link,
                "documents": documents
            })

    except Exception as e:
        print(f"{org} Error: {e}")
        screenshot_path = os.path.join(os.path.dirname(__file__), f"{org.lower().replace(' ', '_')}_screenshot.png")
        try:
            driver.set_window_size(1920, 1080)
            try:
                table = driver.find_element(By.CSS_SELECTOR, row_selector)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
            except:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.save_screenshot(screenshot_path)
            print(f"Saved screenshot: {screenshot_path}")
            img = cv2.imread(screenshot_path)
            if img is None:
                print(f"Failed to load screenshot: {screenshot_path}")
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                table_img = img[y:y+h, x:x+w]
                cv2.imwrite(screenshot_path, table_img)
                print("Cropped to table contour")
            else:
                print("No table contour found")
            text = pytesseract.image_to_string(Image.open(screenshot_path))
            print(f"OCR extracted text for {org}: {text[:200]}...")

            # Parse OCR text
            rfq_pattern = re.compile(r"(RFP\s*#[^\s]+)\s*-\s*(.*?)(?=\n|$)", re.MULTILINE)
            matches = rfq_pattern.findall(text)
            for rfp_number, title in matches:
                due_date_match = re.search(r"(?:End Date|Due Date)[^\n]*\n([^\n]+)", text, re.IGNORECASE)
                due_date = due_date_match.group(1).strip() if due_date_match else ""
                title_lower = title.lower()
                work_type = "unknown"
                if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
                    work_type = "utility/transportation"
                elif any(word in title_lower for word in ["landscaping", "maintenance"]):
                    work_type = "maintenance"
                data.append({
                    "organization": org,
                    "rfp_number": rfp_number.strip(),
                    "title": title.strip(),
                    "work_type": work_type,
                    "open_date": date.today().strftime("%Y-%m-%d"),
                    "due_date": due_date,
                    "status": "Open",
                    "link": url,
                    "documents": []
                })
        except Exception as ocr_e:
            print(f"OCR failed for {org}: {ocr_e}")

driver.switch_to.default_content()
with open("rfqs.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Scraped {len(data)} open RFQs from all sites and saved to rfqs.json")
driver.quit()