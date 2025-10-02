from selenium.webdriver.common.by import By

class ScraperStrategy:
    """Defines different strategies for scraping RFQ tables"""
    
    # Common table row selectors in order of preference
    TABLE_STRATEGIES = [
        {
            "name": "standard_table",
            "row_selector": "table tbody tr",
            "cell_selector": "td",
            "expected_cell_count": [3, 4, 5],
            "description": "Standard HTML table"
        },
        {
            "name": "table_with_class",
            "row_selector": "table.tabHome tbody tr",
            "cell_selector": "td",
            "expected_cell_count": [3, 4, 5],
            "description": "Table with specific class"
        },
        {
            "name": "bonfire_table",
            "row_selector": "tbody tr",
            "cell_selector": "td",
            "expected_cell_count": [3, 4, 5],
            "description": "Bonfire portal table"
        },
        {
            "name": "div_opportunity_item",
            "row_selector": ".opportunity-item",
            "cell_selector": "div, .opportunity-cell",
            "expected_cell_count": [3, 4, 5],
            "description": "Div-based opportunity items"
        },
        {
            "name": "div_opportunity_row",
            "row_selector": ".opportunity-row",
            "cell_selector": "div",
            "expected_cell_count": [3, 4, 5],
            "description": "OpenGov opportunity rows"
        },
        {
            "name": "generic_rows",
            "row_selector": "tr",
            "cell_selector": "td",
            "expected_cell_count": [3, 4, 5],
            "description": "Generic table rows"
        },
        {
            "name": "div_rows",
            "row_selector": "div.row, .item",
            "cell_selector": "div",
            "expected_cell_count": [3, 4, 5],
            "description": "Div-based rows"
        }
    ]
    
    @staticmethod
    def try_strategies(driver, current_selector=None):
        """
        Try different scraping strategies and return the one that works
        
        Returns: dict with strategy info or None
        """
        strategies = ScraperStrategy.TABLE_STRATEGIES.copy()
        
        # If we have a current selector that worked before, try it first
        if current_selector:
            matching_strategy = next(
                (s for s in strategies if s["row_selector"] == current_selector),
                None
            )
            if matching_strategy:
                # Move it to the front
                strategies.remove(matching_strategy)
                strategies.insert(0, matching_strategy)
        
        for strategy in strategies:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, strategy["row_selector"])
                
                if len(rows) > 0:
                    # Check if rows have cells
                    test_row = rows[0]
                    cells = test_row.find_elements(By.CSS_SELECTOR, strategy["cell_selector"])
                    
                    if not cells:
                        # Try alternative cell selector
                        cells = test_row.find_elements(By.TAG_NAME, "td")
                    
                    if not cells:
                        cells = test_row.find_elements(By.TAG_NAME, "div")
                    
                    cell_count = len(cells)
                    
                    # Check if cell count is reasonable
                    if cell_count in strategy["expected_cell_count"] or cell_count >= 3:
                        print(f"✅ Strategy '{strategy['name']}' works: {len(rows)} rows, ~{cell_count} cells")
                        return {
                            "strategy": strategy,
                            "row_count": len(rows),
                            "cell_count": cell_count,
                            "rows": rows
                        }
                    else:
                        print(f"⚠️ Strategy '{strategy['name']}' found rows but cell count wrong: {cell_count}")
                
            except Exception as e:
                print(f"❌ Strategy '{strategy['name']}' failed: {e}")
                continue
        
        return None
    
    @staticmethod
    def detect_pagination(driver):
        """
        Try to detect pagination controls
        
        Returns: dict with pagination info or None
        """
        pagination_selectors = [
            {
                "selector": ".pagination a, .pager a",
                "type": "standard_pagination"
            },
            {
                "selector": "a[rel='next'], a[aria-label*='next' i]",
                "type": "semantic_next"
            },
            {
                "selector": "a[href*='page']",
                "type": "page_links"
            },
            {
                "selector": "button[class*='next' i], button[aria-label*='next' i]",
                "type": "button_next"
            }
        ]
        
        for pag in pagination_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, pag["selector"])
                
                if elements:
                    # Filter out obvious non-pagination elements
                    valid_elements = []
                    for elem in elements:
                        text = (elem.text or elem.get_attribute('title') or '').strip().upper()
                        
                        # Skip column headers
                        if text in ['RFP NUMBER', 'TITLE', 'DUE DATE', 'STATUS', 'DATE', 'SORT']:
                            continue
                        
                        valid_elements.append(elem)
                    
                    if valid_elements:
                        print(f"✅ Found pagination: {pag['type']} ({len(valid_elements)} elements)")
                        return {
                            "type": pag["type"],
                            "selector": pag["selector"],
                            "elements": valid_elements
                        }
            except:
                continue
        
        return None

