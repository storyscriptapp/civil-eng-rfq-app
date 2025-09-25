from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import date

options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.headless = False  # Set to True for production

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

data = []
sites = [
    ("City of Mesa", "https://www.mesaaz.gov/Business-Development/Engineering/Architectural-Engineering-Design-Opportunities", "table tbody tr", 3, True),
    ("City of Yuma", "https://yumaaz.bonfirehub.com/portal/?tab=openOpportunities", ".opportunity-item", 4, True),  # BonfireHub selector
    ("City of Apache Junction", "https://www.apachejunctionaz.gov/826/Current-Solicitations", "table tbody tr", 4, False),  # Static table
    ("Pinal County", "https://pinalcountyaz.bonfirehub.com/portal/?tab=openOpportunities", ".opportunity-item", 4, True),  # BonfireHub
    ("Town of Florence", "https://procurement.opengov.com/portal/florenceaz", ".opportunity-row", 4, True),  # OpenGov
    ("Town of Queen Creek", "https://procurement.opengov.com/portal/queencreekaz", ".opportunity-row", 4, True),  # OpenGov
]

for org, url, row_selector, cell_count, is_dynamic in sites:
    try:
        print(f"Scraping {org}...")
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, row_selector)))
        rows = driver.find_elements(By.CSS_SELECTOR, row_selector)

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.CSS_SELECTOR, ".opportunity-cell")
            if len(cells) < cell_count:
                continue

            title_elem = cells[0].find_element(By.TAG_NAME, "a")
            title = title_elem.text.strip()
            link = title_elem.get_attribute("href")
            if not link.startswith("http"):
                link = url + link
            rfp_number = cells[1].text.strip() if cell_count > 1 else ""
            due_date = cells[2].text.strip()
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
            })

    except Exception as e:
        print(f"{org} Error: {e}")

with open("rfqs.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Scraped {len(data)} open RFQs from all sites and saved to rfqs.json")
driver.quit()