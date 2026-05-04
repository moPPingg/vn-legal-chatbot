"""Item definitions for the VBPL crawler."""

import scrapy


class VbplItem(scrapy.Item):
    """Optional structured item model.

    The current spider yields plain dictionaries for flexibility.
    Keep this class for teams that prefer explicit Scrapy item schemas.
    """
