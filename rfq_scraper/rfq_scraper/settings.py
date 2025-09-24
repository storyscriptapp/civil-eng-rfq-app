BOT_NAME = "rfq_scraper"
SPIDER_MODULES = ["rfq_scraper.spiders"]
NEWSPIDER_MODULE = "rfq_scraper.spiders"
ADDONS = {}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 5
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.gilbertaz.gov/",
}
FEED_EXPORT_ENCODING = "utf-8"
FEEDS = {
    'rfqs.json': {
        'format': 'json',
        'indent': 4,
    }
}
DOWNLOADER_MIDDLEWARES = {
    "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler": 800,
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000