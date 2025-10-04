from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import json
from datetime import date
import time
import os
import argparse
from PIL import Image
import pytesseract
import cv2
import re
from scraper_health import ScraperHealthMonitor
from scraper_strategies import ScraperStrategy
from job_tracking import RFQJobTracker
from scraper_checkpoint import ScraperCheckpoint

# Parse command line arguments
parser = argparse.ArgumentParser(description='RFQ Scraper with checkpoint support')
parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
parser.add_argument('--fresh', action='store_true', help='Start fresh, ignore checkpoint')
parser.add_argument('--cities', type=str, help='Comma-separated list of city names to scrape')
args = parser.parse_args()

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load cities
with open("cities.json", "r") as f:
    sites = json.load(f)

# Filter cities if --cities argument provided
if args.cities:
    selected_city_names = [name.strip() for name in args.cities.split(',')]
    sites = [city for city in sites if city['organization'] in selected_city_names]
    print(f"\n{'='*60}")
    print(f"Scraping SELECTED cities: {len(sites)}")
    print(f"Cities: {', '.join([c['organization'] for c in sites])}")
    print(f"{'='*60}\n")

# Initialize checkpoint system
checkpoint = ScraperCheckpoint()

# Handle checkpoint flags
if args.fresh:
    checkpoint.reset()
elif args.resume:
    resume_info = checkpoint.get_resume_info()
    if resume_info["should_resume"]:
        print(f"\n📍 RESUMING from checkpoint:")
        print(f"   Last completed: {resume_info['last_city']}")
        print(f"   Starting from city #{resume_info['resume_from_index'] + 1}")
        print(f"   Timestamp: {resume_info['timestamp']}\n")
    else:
        print("No checkpoint found - starting fresh")

# Initialize health monitor and job tracker
health_monitor = ScraperHealthMonitor()
job_tracker = RFQJobTracker()
cities_config_updated = False  # Track if we need to save cities.json

options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.headless = False
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")

def create_driver():
    """Create a new Chrome driver instance"""
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def create_undetected_driver():
    """Create undetected Chrome driver for Cloudflare-protected sites"""
    uc_options = uc.ChromeOptions()
    uc_options.add_argument("--window-size=1920,1080")
    uc_options.add_argument("--disable-blink-features=AutomationControlled")
    # Use version_main=140 to match Chrome 140.x
    driver = uc.Chrome(options=uc_options, version_main=140)
    return driver

driver = create_driver()

data = []

for site_idx, site in enumerate(sites):
    org = site["organization"]
    url = site["url"]
    row_selector = site["row_selector"]
    cell_count = site["cell_count"]
    is_dynamic = site["is_dynamic"]
    manual = site.get("manual", False)
    has_pagination = site.get("has_pagination", False)
    pagination_selector = site.get("pagination_selector", "")
    skip_wait = site.get("skip_wait", False)
    uses_cloudflare = site.get("uses_cloudflare", False)
    
    rfq_count_for_city = 0
    strategy_used = None
    scrape_error = None
    city_data = []  # Store this city's RFQs separately

    # Check if we should skip this city (checkpoint)
    if checkpoint.should_skip_city(site_idx, org):
        print(f"⏭️  Skipping {org} (already completed in this run)")
        continue

    if manual:
        print(f"Scraping {org} (manual CAPTCHA required)...")
        input(f"Press Enter after resolving CAPTCHA for {org} or skip...")
        time.sleep(2)

    try:
        # Switch to undetected driver for Cloudflare-protected sites
        if uses_cloudflare:
            print(f"🛡️ {org} uses Cloudflare - switching to undetected driver...")
            try:
                driver.quit()
            except:
                pass
            driver = create_undetected_driver()
            time.sleep(2)  # Give the undetected driver time to start
        else:
            # Check if browser is still alive, restart if needed
            try:
                driver.current_url  # This will fail if session is dead
            except:
                print(f"⚠️ Browser session died, restarting...")
                try:
                    driver.quit()
                except:
                    pass
                driver = create_driver()
        
        print(f"Scraping {org}...")
        driver.get(url)
        
        # Give Cloudflare time to verify the browser
        if uses_cloudflare:
            print(f"⏳ Waiting for Cloudflare verification...")
            time.sleep(8)  # Wait for Cloudflare check to complete
            # Try to detect and wait for Cloudflare challenge to pass
            try:
                wait_cf = WebDriverWait(driver, 15)
                # Check if Cloudflare challenge is present
                if "cf-browser-verification" in driver.page_source or "Just a moment" in driver.page_source:
                    print(f"🔄 Cloudflare challenge detected, waiting...")
                    time.sleep(5)
            except:
                pass
            print(f"✓ Cloudflare verification complete")
        
        wait = WebDriverWait(driver, 30)
        
        if skip_wait:
            print(f"Skipping wait for {org}, loading directly...")
            time.sleep(5)  # Just wait for page to settle
        else:
            # Scroll to table
            try:
                table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, row_selector)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
                time.sleep(2)
                print(f"Table found for {org}")
            except Exception as e:
                print(f"Table not found for {org}, trying scroll: {e}")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

        # Handle iframes (only if not explicitly disabled)
        uses_iframe = site.get("uses_iframe", True)  # Default to True for backward compatibility
        if is_dynamic and uses_iframe:
            try:
                iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                driver.switch_to.frame(iframe)
                print(f"✅ Switched to iframe for {org}")
                # BidNet sites need more time for dynamic content
                if 'bidnet' in url.lower():
                    print(f"⏳ BidNet detected - waiting for dynamic table...")
                    time.sleep(8)
                else:
                    time.sleep(2)  # Give iframe content time to load
            except:
                print(f"⚠️ No iframe found for {org}, continuing without iframe")
        elif is_dynamic and not uses_iframe:
            print(f"⏭️  Skipping iframe for {org} (uses_iframe=false)")

        # Pagination loop
        page_num = 1
        seen_titles = set()  # Track titles to detect duplicates
        max_pages = 10  # Safety limit
        
        while page_num <= max_pages:
            print(f"Scraping {org} page {page_num}...")
            time.sleep(1)  # Let page load
            
            # Try to find rows using configured selector first
            rows = driver.find_elements(By.CSS_SELECTOR, row_selector)
            print(f"Found {len(rows)} rows for {org} using configured selector")
            
            # If no rows found, try multi-strategy fallback
            if len(rows) == 0:
                print(f"⚠️ No rows with configured selector. Trying fallback strategies...")
                strategy_result = ScraperStrategy.try_strategies(driver, row_selector)
                
                if strategy_result:
                    rows = strategy_result["rows"]
                    new_selector = strategy_result["strategy"]["row_selector"]
                    strategy_used = strategy_result["strategy"]["name"]
                    
                    # Update cities.json with working strategy
                    if new_selector != row_selector:
                        print(f"📝 Updating {org} config to use '{strategy_used}' strategy")
                        sites[site_idx]["row_selector"] = new_selector
                        sites[site_idx]["cell_count"] = strategy_result["cell_count"]
                        sites[site_idx]["strategy_name"] = strategy_used
                        row_selector = new_selector  # Use for rest of pagination
                        cell_count = strategy_result["cell_count"]
                        cities_config_updated = True
                else:
                    print(f"❌ No working strategy found for {org}")
                    scrape_error = "No working selector strategy found"
                    break
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.CSS_SELECTOR, ".opportunity-cell") or row.find_elements(By.TAG_NAME, "div")
                if len(cells) < cell_count:
                    print(f"Skipping row with {len(cells)} cells (expected {cell_count})")
                    continue

                # Try to find link - might be in different cells for different orgs
                try:
                    title_elem = None
                    link = None
                    title = None
                    
                    # Try to find link in any of the first few cells
                    for i in range(min(len(cells), len(cells))):  # Check all cells
                        try:
                            # First try <a> tag
                            title_elem = cells[i].find_element(By.TAG_NAME, "a")
                            title = title_elem.text.strip().split('\n')[0]
                            link = title_elem.get_attribute("href")
                            if link:
                                if not link.startswith("http"):
                                    link = url.rsplit('/', 1)[0] + '/' + link
                                break
                        except:
                            pass
                        
                        # Try button with data-href or onclick
                        try:
                            button = cells[i].find_element(By.TAG_NAME, "button")
                            link = button.get_attribute("data-href") or button.get_attribute("data-url")
                            if link:
                                title = cells[0].text.strip().split('\n')[0] if i > 0 else button.text.strip()
                                if not link.startswith("http"):
                                    link = url.rsplit('/', 1)[0] + '/' + link
                                break
                        except:
                            pass
                        
                        # Try link inside button
                        try:
                            button_link = cells[i].find_element(By.CSS_SELECTOR, "button a, a button")
                            link = button_link.get_attribute("href")
                            if link:
                                title = cells[0].text.strip().split('\n')[0]
                                if not link.startswith("http"):
                                    link = url.rsplit('/', 1)[0] + '/' + link
                                break
                        except:
                            pass
                    
                    # If still no link, try to construct from row data
                    if not link:
                        # Bonfire URLs often follow pattern: /portal/...opportunityId=XXX
                        # Try to find opportunity ID in row
                        row_html = row.get_attribute("innerHTML")
                        if "opportunityId=" in row_html or "opportunity/" in row_html:
                            import re
                            opp_id_match = re.search(r'opportunityId[=\\/](\d+)', row_html)
                            if opp_id_match:
                                opp_id = opp_id_match.group(1)
                                link = f"{url}&opportunityId={opp_id}"
                                title = cells[0].text.strip().split('\n')[0] if cells else "Unknown"
                    
                    # If no specific link found, use the organization's RFQ page as fallback
                    if not link:
                        link = url  # Use the main RFQ listing page
                        print(f"⚠️ No specific link found for {org}, using main page: {url}")
                    
                    # If no title found, try to extract from cell text
                    if not title and cells:
                        title = cells[0].text.strip().split('\n')[0]
                        if not title:
                            title = f"RFQ from {org}"  # Last resort
                        print(f"⚠️ Extracted title from cell text: {title[:50]}...")
                        
                except Exception as e:
                    print(f"❌ Error extracting title/link: {e}")
                    continue

                try:
                    # Bonfire sites (Yuma, Pinal) have different structure
                    is_bonfire = "bonfire" in url.lower()
                    
                    if is_bonfire:
                        # Bonfire structure: cell[0]=Status, cell[1]=RFP#, cell[2]=Title, cell[3]=Due Date
                        if len(cells) >= 3:
                            status = cells[0].text.strip()
                            rfp_number = cells[1].text.strip()
                            title = cells[2].text.strip()
                            due_date = cells[3].text.strip() if len(cells) > 3 else "N/A"
                            print(f"✅ Bonfire: {rfp_number} - {title[:50]}...")
                        else:
                            print(f"⚠️ Bonfire row has only {len(cells)} cells, expected 6+")
                            rfp_number = "N/A"
                            title = "Unknown RFQ"
                            due_date = "N/A"
                            status = "Open"
                        
                        documents = []
                    else:
                        # Regular sites (Mesa, Gilbert, etc.)
                        rfp_number = cells[0].text.strip().split('\n')[1].replace("Project No. ", "") if '\n' in cells[0].text else cells[1].text.strip()
                        due_date = cells[1].text.strip() if org == "City of Mesa" else cells[2].text.strip()
                        documents = cells[2].text.strip().split('\n') if org == "City of Mesa" and cell_count > 2 else []
                        status = cells[3].text.strip() if cell_count > 3 else "Open"
                        
                except Exception as e:
                    print(f"Error extracting fields: {e}")
                    print(f"Cell 0: {cells[0].text[:100] if cells else 'N/A'}")
                    continue

                title_lower = title.lower()
                work_type = "unknown"
                if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
                    work_type = "utility/transportation"
                elif any(word in title_lower for word in ["landscaping", "maintenance"]):
                    work_type = "maintenance"

                open_date = date.today().strftime("%Y-%m-%d")
                
                # Check for duplicates
                if title in seen_titles:
                    continue  # Skip duplicate
                seen_titles.add(title)
                
                city_data.append({
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
                print(f"✓ Added: {title[:50]}...")
                rfq_count_for_city += 1
            
            # Check for next page
            if has_pagination and page_num < max_pages:
                try:
                    next_buttons = driver.find_elements(By.CSS_SELECTOR, pagination_selector)
                    print(f"Found {len(next_buttons)} potential next page buttons for {org}")
                    
                    clicked = False
                    for next_button in next_buttons:
                        try:
                            if next_button.is_displayed() and next_button.is_enabled():
                                button_text = next_button.text or next_button.get_attribute('title') or next_button.get_attribute('aria-label')
                                
                                # Skip column headers and non-numeric buttons
                                if button_text and button_text.upper() in ['RFP NUMBER', 'TITLE', 'DUE DATE', 'STATUS', 'DATE', 'SORT']:
                                    continue
                                
                                # Only click if it's a number greater than current page or contains "next"
                                if button_text and (button_text.isdigit() and int(button_text) > page_num) or 'next' in button_text.lower():
                                    print(f"Trying to click pagination button: '{button_text}'")
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                                    time.sleep(0.5)
                                    next_button.click()
                                    page_num += 1
                                    time.sleep(3)  # Wait for next page to load
                                    clicked = True
                                    break
                        except Exception as e:
                            print(f"Failed to click button: {e}")
                            continue
                    
                    if not clicked:
                        print(f"No more pages for {org}")
                        break
                except Exception as e:
                    print(f"Pagination error for {org}: {e}")
                    break
            else:
                if page_num >= max_pages:
                    print(f"Reached max pages ({max_pages}) for {org}")
                break

        # Record successful scrape
        health_monitor.record_city_result(
            org, 
            rfq_count_for_city, 
            status="success",
            strategy_used=strategy_used or site.get("strategy_name", "default")
        )
        
    except Exception as e:
        print(f"{org} Error: {e}")
        scrape_error = str(e)
        
        # Record failed scrape
        health_monitor.record_city_result(
            org,
            rfq_count_for_city,
            status="error",
            error=str(e)
        )
        # OCR fallback
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
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            cv2.imwrite(screenshot_path, gray)
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
                city_data.append({
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
    
    # Switch back to regular driver after Cloudflare sites
    if uses_cloudflare:
        print(f"✓ Finished {org}, switching back to regular driver...")
        try:
            driver.quit()
        except:
            pass
        driver = create_driver()
        time.sleep(1)
    
    # Process and save this city's data immediately
    if city_data:
        print(f"💾 Saving {len(city_data)} RFQs for {org} to database...")
        enhanced_city_data = job_tracker.process_scraped_jobs(city_data)
        data.extend(enhanced_city_data)  # Add to global list
        
        # Save updated rfqs.json after each city
        with open("rfqs.json", "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"✅ {org}: {len(city_data)} RFQs saved and checkpoint marked")
    
    # Mark checkpoint after each city (success or failure)
    checkpoint.mark_city_complete(site_idx, org, rfq_count_for_city)

# Final processing - already done incrementally above
print(f"\n📊 Total: {len(data)} RFQs from all cities")
# Note: Data already saved incrementally after each city

# Mark scrape as complete
checkpoint.mark_complete()

# Show job tracking stats
tracking_stats = job_tracker.get_stats()
print(f"\n📈 Job Tracking Stats:")
print(f"   Total jobs in database: {tracking_stats.get('total_jobs', 0)}")
print(f"   New jobs this run: {tracking_stats['by_status'].get('new', 0)}")
print(f"   User ignored: {tracking_stats['by_status'].get('ignore', 0)}")
print(f"   Pursuing: {tracking_stats['by_status'].get('pursuing', 0)}")
print(f"   Completed: {tracking_stats['by_status'].get('completed', 0)}")

# Update cities.json if strategies changed
if cities_config_updated:
    print("\n📝 Updating cities.json with new working strategies...")
    with open("cities.json", "w") as f:
        json.dump(sites, f, indent=4)
    print("✅ cities.json updated")

# Save health monitoring data
health_monitor.save_run()
print("\n" + "="*60)
print("HEALTH REPORT")
print("="*60)
health_monitor.send_notification(method="console")

# Safe cleanup
try:
    driver.switch_to.default_content()
except:
    pass
try:
    driver.quit()
except:
    pass