"""
Auto-detection tool with comparison to existing configs
Analyzes both existing and new cities for validation
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

class CityDetectorCompare:
    def __init__(self):
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.headless = False
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Load existing configs for comparison
        with open("cities.json", 'r') as f:
            self.existing_configs = {city["organization"]: city for city in json.load(f)}
    
    def detect_site(self, organization, url, existing_config=None):
        """Analyze a website and detect configuration"""
        print(f"\n{'='*60}")
        print(f"Analyzing: {organization}")
        print(f"URL: {url}")
        if existing_config:
            print(f"📋 Comparing to existing config...")
        print(f"{'='*60}")
        
        config = {
            "organization": organization,
            "url": url,
            "confidence": "unknown",
            "notes": [],
            "detected": {},
            "existing": existing_config if existing_config else {},
            "matches": {}
        }
        
        try:
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Check for Cloudflare
            cloudflare_detected = "cloudflare" in self.driver.page_source.lower() or "just a moment" in self.driver.page_source.lower()
            config["detected"]["uses_cloudflare"] = cloudflare_detected
            if cloudflare_detected:
                config["notes"].append("⚠️ Cloudflare detected - needs undetected driver")
            
            if existing_config:
                if existing_config.get("uses_cloudflare") == cloudflare_detected:
                    config["matches"]["cloudflare"] = "✅ Match"
                else:
                    config["matches"]["cloudflare"] = f"❌ Mismatch: existing={existing_config.get('uses_cloudflare')}, detected={cloudflare_detected}"
            
            # Check for Bonfire
            is_bonfire = "bonfire" in url.lower()
            if is_bonfire:
                config["notes"].append("✅ Bonfire platform detected")
                config["detected"]["row_selector"] = "tbody tr"
                config["detected"]["cell_count"] = 3
                config["detected"]["is_dynamic"] = True
                config["detected"]["has_pagination"] = True
                config["detected"]["pagination_selector"] = ".pagination a, a[aria-label*='Next'], button[aria-label*='Next']"
                config["confidence"] = "high"
                
                if existing_config:
                    if existing_config.get("row_selector") == "tbody tr" or existing_config.get("row_selector") == "table tbody tr":
                        config["matches"]["row_selector"] = "✅ Match (Bonfire)"
                    else:
                        config["matches"]["row_selector"] = f"❌ Mismatch: existing={existing_config.get('row_selector')}"
                
                return config
            
            # Check for iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            config["detected"]["is_dynamic"] = len(iframes) > 0
            if iframes:
                config["notes"].append(f"🔲 {len(iframes)} iframe(s) found - may need switching")
            
            if existing_config:
                if existing_config.get("is_dynamic") == config["detected"]["is_dynamic"]:
                    config["matches"]["is_dynamic"] = "✅ Match"
                else:
                    config["matches"]["is_dynamic"] = f"❌ Mismatch: existing={existing_config.get('is_dynamic')}, detected={config['detected']['is_dynamic']}"
            
            # Try to detect table structure
            table_found = False
            row_count = 0
            cell_count = 0
            working_selector = None
            
            # Try common selectors
            selectors_to_try = [
                ("tbody tr", "Standard tbody rows"),
                ("table tbody tr", "Full table tbody path"),
                ("table tr", "All table rows"),
                ("table.tabHome tbody tr", "Apache Junction style"),
                (".opportunity-row", "OpenGov opportunity rows"),
                (".row", "Bootstrap rows"),
                ("tr[class*='row']", "Row class variants"),
                ("[role='row']", "Accessibility rows"),
                ("div.row", "Div rows"),
            ]
            
            best_match = None
            best_score = 0
            
            for selector, description in selectors_to_try:
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(rows) > 0:
                        # Filter out header rows
                        data_rows = [r for r in rows if r.find_elements(By.TAG_NAME, "td") or r.find_elements(By.TAG_NAME, "div")]
                        if len(data_rows) > 0:
                            current_row_count = len(data_rows)
                            
                            # Get cell count from first data row
                            first_row = data_rows[0]
                            tds = first_row.find_elements(By.TAG_NAME, "td")
                            divs = first_row.find_elements(By.TAG_NAME, "div")
                            current_cell_count = len(tds) if tds else len(divs)
                            
                            # Score this match
                            score = current_row_count
                            if existing_config and selector == existing_config.get("row_selector"):
                                score += 1000  # Boost if matches existing
                            
                            if score > best_score:
                                best_score = score
                                best_match = {
                                    "selector": selector,
                                    "description": description,
                                    "row_count": current_row_count,
                                    "cell_count": current_cell_count,
                                    "cells": tds if tds else divs
                                }
                            
                            print(f"  ✓ {description}: {current_row_count} rows, {current_cell_count} cells (score: {score})")
                            
                except Exception as e:
                    continue
            
            if best_match:
                table_found = True
                config["detected"]["row_selector"] = best_match["selector"]
                config["detected"]["cell_count"] = best_match["cell_count"]
                config["confidence"] = "high" if best_match["row_count"] > 0 else "medium"
                config["notes"].append(f"✅ {best_match['description']}: {best_match['row_count']} rows, {best_match['cell_count']} cells")
                
                # Get sample data
                if len(best_match["cells"]) > 0:
                    sample = " | ".join([c.text[:30] for c in best_match["cells"][:3]])
                    config["notes"].append(f"📋 Sample: {sample}")
                
                # Compare with existing
                if existing_config:
                    if existing_config.get("row_selector") == best_match["selector"]:
                        config["matches"]["row_selector"] = "✅ Exact match"
                    elif existing_config.get("row_selector") in ["tbody tr", "table tbody tr"] and best_match["selector"] in ["tbody tr", "table tbody tr"]:
                        config["matches"]["row_selector"] = "✅ Close match (tbody variants)"
                    else:
                        config["matches"]["row_selector"] = f"⚠️ Different: existing='{existing_config.get('row_selector')}', detected='{best_match['selector']}'"
                    
                    if existing_config.get("cell_count") == best_match["cell_count"]:
                        config["matches"]["cell_count"] = "✅ Match"
                    else:
                        config["matches"]["cell_count"] = f"⚠️ Different: existing={existing_config.get('cell_count')}, detected={best_match['cell_count']}"
            else:
                config["notes"].append("❌ No table found with standard selectors")
                config["confidence"] = "low"
                config["detected"]["row_selector"] = "tbody tr"  # Default guess
                config["detected"]["cell_count"] = 4  # Default guess
                config["detected"]["manual"] = True
            
            # Check for pagination
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, ".pagination, .pager, [class*='pag']")
            config["detected"]["has_pagination"] = len(pagination_elements) > 0
            if pagination_elements:
                config["detected"]["pagination_selector"] = ".pagination a, .pager a, a[href*='page']"
                config["notes"].append("📄 Pagination detected")
            
            if existing_config:
                if existing_config.get("has_pagination") == config["detected"]["has_pagination"]:
                    config["matches"]["has_pagination"] = "✅ Match"
                else:
                    config["matches"]["has_pagination"] = f"⚠️ Different: existing={existing_config.get('has_pagination')}, detected={config['detected']['has_pagination']}"
            
            # Screenshot for manual review
            screenshot_path = f"compare_{organization.replace(' ', '_').lower()}.png"
            self.driver.save_screenshot(screenshot_path)
            config["notes"].append(f"📸 Screenshot: {screenshot_path}")
            
        except Exception as e:
            config["notes"].append(f"❌ Error: {str(e)}")
            config["confidence"] = "error"
        
        return config
    
    def analyze_batch(self, city_list):
        """Analyze multiple cities from a list"""
        results = []
        
        for organization, url in city_list:
            existing = self.existing_configs.get(organization)
            config = self.detect_site(organization, url, existing)
            results.append(config)
            
            # Print summary
            print(f"\n📊 Configuration Summary for {config['organization']}:")
            print(f"   Confidence: {config['confidence']}")
            
            if existing:
                print(f"\n   🔍 COMPARISON:")
                for key, match_result in config.get('matches', {}).items():
                    print(f"      {key}: {match_result}")
            
            print(f"\n   📋 Detected Config:")
            for key, value in config.get('detected', {}).items():
                print(f"      {key}: {value}")
            
            print(f"\n   📝 Notes:")
            for note in config['notes']:
                print(f"      {note}")
            
            time.sleep(2)  # Be nice to servers
        
        self.driver.quit()
        return results
    
    def save_results(self, results, filename="detected_cities_compare.json"):
        """Save analysis results to JSON"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n✅ Results saved to {filename}")


# Main execution
if __name__ == "__main__":
    # Existing cities (for validation)
    existing_cities = [
        ("City of Gilbert", "https://www.gilbertaz.gov/how-do-i/view/rfp-cip-open-bids"),
        ("City of Mesa", "https://www.mesaaz.gov/Business-Development/Engineering/Architectural-Engineering-Design-Opportunities"),
        ("City of Apache Junction", "https://www.apachejunctionaz.gov/826/Current-Solicitations"),
        ("City of Yuma", "https://yumaaz.bonfirehub.com/portal/?tab=openOpportunities"),
        ("Pinal County", "https://pinalcountyaz.bonfirehub.com/portal/?tab=openOpportunities"),
    ]
    
    # New counties to add
    new_cities = [
        ("Maricopa County", "https://www.maricopa.gov/2190/Solicitations"),
        ("Pima County", "https://www.pima.gov/199/Solicitations"),
        ("Yavapai County", "https://www.yavapaiaz.gov/County-Government/Bids"),
        ("Coconino County", "https://www.coconino.az.gov/Bids.aspx"),
        ("Gila County", "https://www.gilacountyaz.gov/government/finance/procurement/current_bids.php"),
        ("Santa Cruz County", "https://www.santacruzcountyaz.gov/286/Bids-Solicitations"),
        ("Graham County", "https://www.graham.az.gov/Bids.aspx"),
        ("Yuma County", "https://www.yumacountyaz.gov/i-want-to/view-request-for-proposals"),
    ]
    
    print("="*60)
    print("🔍 CITY DETECTOR - COMPARISON MODE")
    print("="*60)
    print(f"\n📋 Analyzing {len(existing_cities)} existing cities (validation)")
    print(f"📋 Analyzing {len(new_cities)} new cities")
    print(f"📊 Total: {len(existing_cities) + len(new_cities)} cities\n")
    
    detector = CityDetectorCompare()
    
    print("\n" + "="*60)
    print("PART 1: VALIDATING EXISTING CITIES")
    print("="*60)
    existing_results = detector.analyze_batch(existing_cities)
    
    print("\n" + "="*60)
    print("PART 2: DETECTING NEW CITIES")
    print("="*60)
    new_results = detector.analyze_batch(new_cities)
    
    all_results = existing_results + new_results
    detector.save_results(all_results)
    
    # Summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY (Existing Cities)")
    print("="*60)
    for result in existing_results:
        print(f"\n{result['organization']}:")
        matches = result.get('matches', {})
        if matches:
            match_count = sum(1 for v in matches.values() if '✅' in str(v))
            total = len(matches)
            print(f"  {match_count}/{total} attributes matched")
            for key, value in matches.items():
                if '❌' in str(value) or '⚠️' in str(value):
                    print(f"    - {value}")
    
    print("\n" + "="*60)
    print("🎯 NEW CITIES READY TO ADD")
    print("="*60)
    for result in new_results:
        if result['confidence'] in ['high', 'medium']:
            print(f"\n✅ {result['organization']} - {result['confidence']} confidence")
            print(f"   Selector: {result.get('detected', {}).get('row_selector')}")
            print(f"   Cells: {result.get('detected', {}).get('cell_count')}")

