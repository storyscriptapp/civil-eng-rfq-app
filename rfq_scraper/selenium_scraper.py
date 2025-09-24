from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import date

# Setup Chrome options to mimic a real browser
options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.headless = False  # Set to True for production (no window)

# Initialize driver
driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    driver.get("https://www.gilbertaz.gov/how-do-i/view/rfp-cip-open-bids")

    # Wait for the table to load
    wait = WebDriverWait(driver, 10)
    table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    # Extract rows
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) < 4:
            continue

        rfp_number = cells[0].text.strip()
        title_elem = cells[1].find_element(By.TAG_NAME, "a")
        title = title_elem.text.strip()
        detail_link = title_elem.get_attribute("href")
        if not detail_link.startswith("http"):
            detail_link = "https://www.gilbertaz.gov" + detail_link
        due_date = cells[2].text.strip()
        status = cells[3].text.strip()

        if status != "Open":
            continue

        # Infer work_type
        title_lower = title.lower()
        work_type = "unknown"
        if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
            work_type = "utility/transportation"
        elif any(word in title_lower for word in ["landscaping", "maintenance"]):
            work_type = "maintenance"

        open_date = date.today().strftime("%Y-%m-%d")

        data.append({
            "organization": "City of Gilbert",
            "rfp_number": rfp_number,
            "title": title,
            "work_type": work_type,
            "open_date": open_date,
            "due_date": due_date,
            "status": status,
            "link": detail_link,
        })

    # Save to rfqs.json
    with open("rfqs.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Scraped {len(data)} open RFQs and saved to rfqs.json")

except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
    from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import date

# Setup Chrome options
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

try:
    driver.get("https://www.gilbertaz.gov/how-do-i/view/rfp-cip-open-bids")
    wait = WebDriverWait(driver, 10)

    while True:
        # Wait for table
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 4:
                continue

            rfp_number = cells[0].text.strip()
            title_elem = cells[1].find_element(By.TAG_NAME, "a")
            title = title_elem.text.strip()
            link = title_elem.get_attribute("href")
            if not link.startswith("http"):
                link = "https://www.gilbertaz.gov" + link
            due_date = cells[2].text.strip()
            status = cells[3].text.strip()

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
                "organization": "City of Gilbert",
                "rfp_number": rfp_number,
                "title": title,
                "work_type": work_type,
                "open_date": open_date,
                "due_date": due_date,
                "status": status,
                "link": link,
            })

        # Check for "Next" button
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next")))
            next_button.click()
            wait.until(EC.staleness_of(table))  # Wait for table to refresh
        except:
            print("No more pages to scrape")
            break

    # Save to rfqs.json
    with open("rfqs.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Scraped {len(data)} open RFQs and saved to rfqs.json")

except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()