import scrapy


class GilbertScraperSpider(scrapy.Spider):
    name = "gilbert_scraper"
    allowed_domains = ["gilbertaz.gov"]
    start_urls = ["https://gilbertaz.gov"]

    def parse(self, response):
        pass
