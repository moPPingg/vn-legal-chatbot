from pathlib import Path

import scrapy


class VbplSpider(scrapy.Spider):
    """Crawl VBPL content pages and extract HTML content."""

    name = "vbpl_content"

    def __init__(self, seed_file=None, seed_ids="1", *args, **kwargs):
        super().__init__(*args, **kwargs)
        if seed_file:
            self.seed_ids = [
                line.strip()
                for line in Path(seed_file).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            self.seed_ids = [item_id.strip() for item_id in str(seed_ids).split(",")]

    def start_requests(self):
        """Start crawling from seed IDs."""
        for item_id in self.seed_ids:
            yield scrapy.Request(
                f"https://vbpl.vn/tw/Pages/vbpq-print.aspx?ItemID={item_id}",
                callback=self.parse,
                cb_kwargs={"doc_id": item_id},
            )

    def parse(self, response, doc_id):
        """Extract content from #content element."""
        # Skip if URL was redirected (not the vbpq-print URL anymore)
        if "vbpq-print.aspx" not in response.url:
            return

        content_html = response.css("#content").get()
        # Only yield if content is not empty
        if content_html and content_html.strip():
            yield {
                "id": doc_id,
                "content_html": content_html,
            }
