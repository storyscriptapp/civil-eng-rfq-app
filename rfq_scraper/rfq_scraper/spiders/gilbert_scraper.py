import scrapy
from scrapy_playwright.page import PageMethod

class GilbertScraperSpider(scrapy.Spider):
    name = "gilbert_scraper"
    allowed_domains = ["gilbertaz.gov"]
    start_urls = ["https://www.gilbertaz.gov/how-do-i/view/rfp-cip-open-bids"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 5,
        "ROBOTSTXT_OBEY": True,
    }

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={"playwright": True, "playwright_include_page": True},
                callback=self.parse,
            )

    async def parse(self, response):
        for row in response.css("table tbody tr"):
            title_link = row.css("td:nth-child(2) a::text").get()
            if not title_link:
                continue

            rfp_number = row.css("td:nth-child(1)::text").get().strip()
            title = title_link.strip()
            due_date = row.css("td:nth-child(3)::text").get().strip()
            status = row.css("td:nth-child(4)::text").get().strip()
            detail_link = response.urljoin(row.css("td:nth-child(2) a::attr(href)").get())

            title_lower = title.lower()
            work_type = "unknown"
            if any(word in title_lower for word in ["utility", "irrigation", "sewer", "transportation", "road", "bridge", "hydraulics", "storm drain"]):
                work_type = "utility/transportation"
            elif any(word in title_lower for word in ["landscaping", "maintenance"]):
                work_type = "maintenance"

            open_date = "2025-09-24"
            yield {
                "organization": "City of Gilbert",
                "rfp_number": rfp_number,
                "title": title,
                "work_type": work_type,
                "open_date": open_date,
                "due_date": due_date,
                "status": status,
                "link": detail_link,
            }

        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                meta={"playwright": True, "playwright_include_page": True},
                callback=self.parse,
            )