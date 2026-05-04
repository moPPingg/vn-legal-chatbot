import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import scrapy

# Base URLs for dynamic construction
BASE_URL = "https://vbpl.vn"
METADATA_URL_TEMPLATE = f"{BASE_URL}/TW/Pages/vbpq-thuoctinh.aspx?ItemID={{}}"
LUOCDO_URL_TEMPLATE = f"{BASE_URL}/ninhbinh/Pages/vbpq-luocdo.aspx?ItemID={{}}"


class VbplSpider(scrapy.Spider):
    """Crawl VBPL metadata pages and relationship graph from seed ItemIDs."""

    name = "vbpl"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        proxy_file = kwargs.get("proxy_file")
        if proxy_file:
            crawler.settings.set("PROXY_LIST_FILE", proxy_file, priority="spider")
        else:
            mw = dict(crawler.settings.getwithbase("DOWNLOADER_MIDDLEWARES"))
            mw.pop("vbpl.middlewares.RotatingProxyMiddleware", None)
            crawler.settings.set("DOWNLOADER_MIDDLEWARES", mw, priority="spider")
        return super().from_crawler(crawler, *args, **kwargs)

    def __init__(
        self,
        seed_ids="1",
        seed_file=None,
        proxy_file=None,
        resume=0,
        resume_from="data.jsonl",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.proxy_file = proxy_file
        if seed_file:
            self.seed_ids = [
                line.strip()
                for line in Path(seed_file).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            self.seed_ids = [item_id.strip() for item_id in str(seed_ids).split(",")]
        self.seen_ids = set()
        if int(resume):
            resume_path = Path(resume_from)
            if resume_path.exists():
                for line in resume_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        try:
                            item = json.loads(line)
                            if "id" in item:
                                self.seen_ids.add(str(item["id"]))
                        except json.JSONDecodeError:
                            pass
                self.logger.info(
                    "Resume mode: loaded %d already-scraped IDs from %s",
                    len(self.seen_ids),
                    resume_from,
                )

    async def start(self):
        """Scrapy 2.13+ entry point when custom start_requests() is used."""
        for request in self.start_requests():
            yield request

    def start_requests(self):
        """Start crawling from seed IDs."""
        for item_id in self.seed_ids:
            self.seen_ids.add(item_id)
            yield scrapy.Request(
                METADATA_URL_TEMPLATE.format(item_id),
                callback=self.parse_metadata,
                cb_kwargs={"doc_id": item_id, "content_html": None},
            )

    def _request_if_new(self, item_id):
        """Return a Request for item_id if not already seen, else None."""
        if item_id not in self.seen_ids:
            self.seen_ids.add(item_id)
            return scrapy.Request(
                METADATA_URL_TEMPLATE.format(item_id),
                callback=self.parse_metadata,
                cb_kwargs={"doc_id": item_id, "content_html": None},
            )

    @staticmethod
    def clean_text(extracted_data):
        """Helper to clean up whitespace, tabs, and newlines from HTML text."""
        if not extracted_data:
            return None
        if isinstance(extracted_data, str):
            return extracted_data.strip()

        cleaned = [text.strip() for text in extracted_data if text.strip()]
        return " ".join(cleaned) if cleaned else None

    def _get_table_value(self, response, label_name, offset=1):
        """Helper to extract values from the metadata table based on the label."""
        xpath_query = f'//td[contains(text(), "{label_name}")]/following-sibling::td[{offset}]//text()'
        return self.clean_text(response.xpath(xpath_query).getall())

    def parse_metadata(self, response, doc_id, content_html=None):
        """Extract metadata and continue to relationship page for the same document."""
        if "vbpq-thuoctinh.aspx" in response.url:
            title = self.clean_text(
                response.xpath(
                    '(//div[@class="vbProperties"]//td[@class="title"])[1]//text()'
                ).getall()
            )

            if title:
                item_data = {
                    "id": doc_id,
                    "title": title,
                    "so_ky_hieu": self._get_table_value(response, "Số ký hiệu"),
                    "ngay_ban_hanh": self._get_table_value(response, "Ngày ban hành"),
                    "loai_van_ban": self._get_table_value(response, "Loại văn bản"),
                    "ngay_co_hieu_luc": self._get_table_value(
                        response, "Ngày có hiệu lực"
                    ),
                    "ngay_het_hieu_luc": self._get_table_value(
                        response, "Ngày hết hiệu lực"
                    ),
                    "nguon_thu_thap": self._get_table_value(
                        response, "Nguồn thu thập"
                    ),
                    "ngay_dang_cong_bao": self._get_table_value(
                        response, "Ngày đăng công báo"
                    ),
                    "nganh": self._get_table_value(response, "Ngành"),
                    "linh_vuc": self._get_table_value(response, "Lĩnh vực"),
                    "co_quan_ban_hanh": self._get_table_value(
                        response, "Cơ quan ban hành"
                    ),
                    "chuc_danh": self._get_table_value(
                        response, "Cơ quan ban hành", offset=2
                    ),
                    "nguoi_ky": self._get_table_value(
                        response, "Cơ quan ban hành", offset=3
                    ),
                    "pham_vi": self._get_table_value(response, "Phạm vi"),
                    "thong_tin_ap_dung": self._get_table_value(
                        response, "Thông tin áp dụng"
                    ),
                    "tinh_trang_hieu_luc": self.clean_text(
                        response.xpath(
                            '//div[@class="vbInfo"]//li[@class="red"]/text()'
                        ).get()
                    ),
                    "content": content_html,
                }

                # Fetch the relationship graph block for linked documents.
                yield scrapy.Request(
                    url=LUOCDO_URL_TEMPLATE.format(doc_id),
                    callback=self.parse_luocdo,
                    cb_kwargs={"item_data": item_data},
                )
            else:
                self.logger.debug("Skipping %s: missing document title", doc_id)
        else:
            self.logger.debug("Skipping non-metadata page: %s", response.url)

    def parse_luocdo(self, response, item_data):
        """Step 3: Extract document relationships and yield the final item."""
        if "vbpq-luocdo.aspx" in response.url:
            relationships = {}
            blocks = response.xpath('//div[contains(@class, "luocdo")]')

            for block in blocks:
                title_nodes = block.xpath(
                    './/div[starts-with(@class, "title")]//text()'
                ).getall()
                raw_title = " ".join(
                    [text.strip() for text in title_nodes if text.strip() != "\xa0"]
                )
                rel_title = re.sub(r"\s*\(\d+\)$", "", raw_title).strip()

                doc_items = block.xpath('.//div[@class="content"]//li')
                if not doc_items:
                    continue

                doc_list = []
                for doc in doc_items:
                    doc_href = doc.xpath("./a[1]/@href").get()
                    if doc_href and doc_href != "#":
                        parsed_href = urlparse(doc_href)
                        query_params = parse_qs(parsed_href.query)
                        item_ids = query_params.get("ItemID")
                        if item_ids:
                            doc_list.append(item_ids[0])

                if doc_list:
                    relationships[rel_title] = doc_list

            item_data["relationships"] = relationships
            yield item_data

            for doc_ids in relationships.values():
                for doc_id in doc_ids:
                    req = self._request_if_new(doc_id)
                    if req:
                        yield req
        else:
            self.logger.debug("Skipping non-luocdo page: %s", response.url)
