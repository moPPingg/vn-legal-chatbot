"""Pipelines for post-processing scraped items."""


class VbplPipeline:
    """Pass-through pipeline.

    Enable in settings when you need centralized item validation or cleanup.
    """

    def process_item(self, item, spider):
        return item
