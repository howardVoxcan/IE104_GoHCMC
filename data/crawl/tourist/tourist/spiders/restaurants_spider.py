import scrapy
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class RestaurantsSpider(scrapy.Spider):
    name = "restaurants"
    start_url = "https://us.trip.com/restapi/soa2/18361/foodListSearch"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # setup selenium
        options = webdriver.ChromeOptions()
        options.add_argument("--headless") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(service=Service("/opt/homebrew/bin/chromedriver"), options=options)

    def closed(self, reason):
        """Đóng driver khi spider kết thúc"""
        if self.driver:
            self.driver.quit()

    def start_requests(self):
        payload = self.build_payload(page_index=0)
        yield scrapy.Request(
            url=self.start_url,
            method="POST",
            headers=self.headers,
            body=json.dumps(payload),
            callback=self.parse,
            meta={"page_index": 0}
        )

    def build_payload(self, page_index: int):
        return {
            "districtId": 434,
            "pageIndex": page_index,
            "scence": 1,
            "pageSize": 30,
            "filterType": 2,
            "lat": 0,
            "lon": 0,
            "popularArea": -1,
            "head": {
                "cid": "09034128116461760750",
                "ctok": "",
                "cver": "1.0",
                "lang": "01",
                "sid": "8888",
                "syscode": "09",
                "auth": "",
                "xsid": "",
                "extension": [
                    {"name": "locale", "value": "en-US"},
                    {"name": "currency", "value": "USD"},
                    {"name": "platform", "value": "Online"},
                    {"name": "channel_type", "value": "online"},
                    {"name": "X-Request-Source", "value": ""}
                ],
                "Locale": "en-US",
                "Language": "en",
                "Currency": "USD",
                "ClientID": "09034128116461760750"
            }
        }

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def parse(self, response):
        page_index = response.meta["page_index"]
        data = response.json()

        results = data.get("results", [])
        if not results:
            self.logger.info(f"🚫 Không còn dữ liệu, dừng crawl tại trang {page_index}")
            return

        for item in results:
            name = item.get("englishName", "")
            img = item.get("coverImgaeUrl", "")
            rating = item.get("rating", "")
            review_count = item.get("reviewCount", "")
            price = item.get("price", 0)

            short_desc = ""
            if item.get("rankings"):
                short_desc = item["rankings"][0].get("recommendReason", "")

            long_desc = ""
            if item.get("commentInfo"):
                if isinstance(item["commentInfo"], list) and item["commentInfo"]:
                    long_desc = item["commentInfo"][0].get("content", "")

            short_desc = self.clean_text(short_desc)
            long_desc = self.clean_text(long_desc)

            coordinate = f'{item.get("gglat", "")}, {item.get("gglon", "")}'
            url = "https://us.trip.com" + item.get("jumpUrl", "")

            meta = {
                "name": name,
                "img": img,
                "rating": rating,
                "review_count": review_count,
                "price": price,
                "short_desc": short_desc,
                "long_desc": long_desc,
                "coordinate": coordinate,
            }

            yield response.follow(url, callback=self.parse_item, meta=meta)

        # next page
        next_page = page_index + 1
        payload = self.build_payload(page_index=next_page)
        yield scrapy.Request(
            url=self.start_url,
            method="POST",
            headers=self.headers,
            body=json.dumps(payload),
            callback=self.parse,
            meta={"page_index": next_page}
        )

    def parse_item(self, response):
        name = response.meta.get("name")
        img = response.meta.get("img")
        rating = response.meta.get("rating")
        review_count = response.meta.get("review_count")
        short_desc = response.meta.get("short_desc")
        long_desc = response.meta.get("long_desc")
        coordinate = response.meta.get("coordinate")
        price = response.meta.get("price")

        # lấy address an toàn
        address_parts = response.css("div.gl-poi-detail_info div div::text").getall()
        address = self.clean_text(address_parts[1]) if len(address_parts) > 1 else ""

        # 👉 dùng selenium để lấy opening hours
        self.driver.get(response.url)

        try:
            # chờ nút Opening Hours và click
            btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".gl-poi-detail_time"))
            )
            btn.click()
            time.sleep(1)
        except Exception:
            pass

        # lấy opening hours sau khi click
        html = self.driver.page_source
        sel = scrapy.Selector(text=html)

        opening_times = sel.css(".gl-format-weekday span::text").getall()
        opening_times = "_".join(opening_times)

        yield {
            "name": self.clean_text(name),
            "img": img,
            "rating": rating,
            "review_count": review_count,
            "short_desc": short_desc,
            "long_desc": long_desc,
            "coordinate": coordinate,
            "address": address,
            "price": price,
            "opening_times": opening_times
        }
