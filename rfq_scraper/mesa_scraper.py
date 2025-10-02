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
options.headless = False

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    driver.get("https://www.mesaaz.gov/Business-Development/Engineering/Architectural-Engineering-Design-Opportunities")
    wait = WebDriverWait(driver, 10)
    table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) < 3:
            continue

        title_elem = cells[0].find_element(By.TAG_NAME, "a")
        title = title_elem.text.strip().split('\n')[0]  # Remove "Project No." suffix
        link = title_elem.get_attribute("href")
        if not link.startswith("http"):
            link = "https://www.mesaaz.gov" + link
        due_date = cells[1].text.strip()  # Correct: Due Date is second column
        rfp_number = cells[0].text.strip().split('\n')[1].replace("Project No. ", "")  # Extract project number
        status = "Open"  # Mesa lists open RFQs
        documents = cells[2].text.strip().split('\n')  # Capture related documents

        title_lower = title.lower()
        work_type = "unknown"
        if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
            work_type = "utility/transportation"
        elif any(word in title_lower for word in ["landscaping", "maintenance"]):
            work_type = "maintenance"

        open_date = date.today().strftime("%Y-%m-%d")
        data.append({
            "organization": "City of Mesa",
            "rfp_number": rfp_number,
            "title": title,
            "work_type": work_type,
            "open_date": open_date,
            "due_date": due_date,
            "status": status,
            "link": link,
            "documents": documents  # Add related documents
        })

    with open("rfqs.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Scraped {len(data)} open RFQs and saved to rfqs.json")

except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()