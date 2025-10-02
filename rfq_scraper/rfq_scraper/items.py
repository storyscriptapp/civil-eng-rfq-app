# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RfqScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    work_type = scrapy.Field()
    open_date = scrapy.Field()
    due_date = scrapy.Field()
    details_link = scrapy.Field()
