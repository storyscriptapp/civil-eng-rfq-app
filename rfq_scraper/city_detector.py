"""
Auto-detection tool for new city configurations
Analyzes procurement websites and generates draft configs
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

class CityDetector:
    def __init__(self):
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.headless = False
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def detect_site(self, organization, url):
        """Analyze a website and detect configuration"""
        print(f"\n{'='*60}")
        print(f"Analyzing: {organization}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        config = {
            "organization": organization,
            "url": url,
            "confidence": "unknown",
            "notes": []
        }
        
        try:
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Check for Cloudflare
            if "cloudflare" in self.driver.page_source.lower() or "just a moment" in self.driver.page_source.lower():
                config["uses_cloudflare"] = True
                config["notes"].append("⚠️ Cloudflare detected - needs undetected driver")
            else:
                config["uses_cloudflare"] = False
            
            # Check for Bonfire
            if "bonfire" in url.lower():
                config["notes"].append("✅ Bonfire platform detected")
                config["row_selector"] = "tbody tr"
                config["cell_count"] = 3
                config["is_dynamic"] = True
                config["has_pagination"] = True
                config["pagination_selector"] = ".pagination a, a[aria-label*='Next'], button[aria-label*='Next']"
                config["confidence"] = "high"
                return config
            
            # Check for iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                config["is_dynamic"] = True
                config["notes"].append(f"🔲 {len(iframes)} iframe(s) found - may need switching")
            else:
                config["is_dynamic"] = False
            
            # Try to detect table structure
            table_found = False
            row_count = 0
            cell_count = 0
            working_selector = None
            
            # Try common selectors
            selectors_to_try = [
                ("tbody tr", "Standard table rows"),
                ("table tr", "All table rows"),
                (".opportunity-row", "OpenGov opportunity rows"),
                (".row", "Bootstrap rows"),
                ("tr[class*='row']", "Row class variants"),
                ("[role='row']", "Accessibility rows")
            ]
            
            for selector, description in selectors_to_try:
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(rows) > 0:
                        # Filter out header rows
                        data_rows = [r for r in rows if r.find_elements(By.TAG_NAME, "td")]
                        if len(data_rows) > 0:
                            table_found = True
                            row_count = len(data_rows)
                            working_selector = selector
                            
                            # Get cell count from first data row
                            first_row = data_rows[0]
                            cells = first_row.find_elements(By.TAG_NAME, "td")
                            cell_count = len(cells)
                            
                            config["notes"].append(f"✅ {description}: {row_count} rows, {cell_count} cells")
                            print(f"  ✓ Found {row_count} rows using '{selector}' with {cell_count} cells")
                            
                            # Get sample data
                            if len(cells) > 0:
                                sample = " | ".join([c.text[:30] for c in cells[:3]])
                                config["notes"].append(f"📋 Sample: {sample}")
                            
                            break
                except Exception as e:
                    continue
            
            if table_found:
                config["row_selector"] = working_selector
                config["cell_count"] = cell_count
                config["confidence"] = "high" if row_count > 0 else "medium"
            else:
                config["notes"].append("❌ No table found with standard selectors")
                config["confidence"] = "low"
                config["row_selector"] = "tbody tr"  # Default guess
                config["cell_count"] = 4  # Default guess
                config["manual"] = True
            
            # Check for pagination
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, ".pagination, .pager, [class*='pag']")
            if pagination_elements:
                config["has_pagination"] = True
                config["pagination_selector"] = ".pagination a, .pager a, a[href*='page']"
                config["notes"].append("📄 Pagination detected")
            else:
                config["has_pagination"] = False
            
            # Screenshot for manual review
            screenshot_path = f"city_analysis_{organization.replace(' ', '_').lower()}.png"
            self.driver.save_screenshot(screenshot_path)
            config["notes"].append(f"📸 Screenshot saved: {screenshot_path}")
            
        except Exception as e:
            config["notes"].append(f"❌ Error: {str(e)}")
            config["confidence"] = "error"
        
        return config
    
    def analyze_batch(self, city_list):
        """Analyze multiple cities from a list"""
        results = []
        
        for organization, url in city_list:
            config = self.detect_site(organization, url)
            results.append(config)
            
            # Print summary
            print(f"\n📊 Configuration Summary:")
            print(f"   Organization: {config['organization']}")
            print(f"   Selector: {config.get('row_selector', 'N/A')}")
            print(f"   Cell Count: {config.get('cell_count', 'N/A')}")
            print(f"   Dynamic: {config.get('is_dynamic', 'N/A')}")
            print(f"   Cloudflare: {config.get('uses_cloudflare', False)}")
            print(f"   Confidence: {config['confidence']}")
            print(f"\n   Notes:")
            for note in config['notes']:
                print(f"      {note}")
            
            time.sleep(2)  # Be nice to servers
        
        self.driver.quit()
        return results
    
    def save_results(self, results, filename="detected_cities.json"):
        """Save analysis results to JSON"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n✅ Results saved to {filename}")
        
        # Generate draft for cities.json
        print(f"\n📝 Draft entries for cities.json:")
        print("="*60)
        for config in results:
            if config['confidence'] in ['high', 'medium']:
                print(f"    {{")
                print(f"        \"organization\": \"{config['organization']}\",")
                print(f"        \"url\": \"{config['url']}\",")
                print(f"        \"row_selector\": \"{config.get('row_selector', 'tbody tr')}\",")
                print(f"        \"cell_count\": {config.get('cell_count', 4)},")
                print(f"        \"is_dynamic\": {str(config.get('is_dynamic', False)).lower()},")
                print(f"        \"manual\": {str(config.get('manual', False)).lower()}", end="")
                if config.get('has_pagination'):
                    print(",")
                    print(f"        \"has_pagination\": true,")
                    print(f"        \"pagination_selector\": \"{config.get('pagination_selector', '')}\"", end="")
                if config.get('uses_cloudflare'):
                    print(",")
                    print(f"        \"uses_cloudflare\": true", end="")
                print()
                print(f"    }},")
                print()


# Main execution
if __name__ == "__main__":
    cities = [
        ("Maricopa County", "https://www.maricopa.gov/2190/Solicitations"),
        ("Pima County", "https://www.pima.gov/199/Solicitations"),
        ("Yavapai County", "https://www.yavapaiaz.gov/County-Government/Bids"),
        ("Coconino County", "https://www.coconino.az.gov/Bids.aspx"),
        ("Gila County", "https://www.gilacountyaz.gov/government/finance/procurement/current_bids.php"),
        ("Santa Cruz County", "https://www.santacruzcountyaz.gov/286/Bids-Solicitations"),
        ("Graham County", "https://www.graham.az.gov/Bids.aspx"),
        ("Yuma County", "https://www.yumacountyaz.gov/i-want-to/view-request-for-proposals"),
    ]
    
    detector = CityDetector()
    results = detector.analyze_batch(cities)
    detector.save_results(results)
    
    print("\n" + "="*60)
    print("🎯 Analysis Complete!")
    print("="*60)
    print("\n📝 Next steps:")
    print("1. Review screenshots in rfq_scraper/ folder")
    print("2. Check detected_cities.json for full analysis")
    print("3. Copy high-confidence entries to cities.json")
    print("4. Test scrape each new city individually")
    print("5. Adjust selectors as needed")

