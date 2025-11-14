import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json


def clean_text(text, mode="remove"):
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    return text


def get_open_hours(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(20)

    try:
        print(f"Loading {url}")
        driver.get(url)
        time.sleep(3)
        wait = WebDriverWait(driver, 10)
        btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".one-line .field"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        html = driver.page_source
        sel = scrapy.Selector(text=html)
        opening_times = sel.css(".online-open-time-txt-ctt::text").get()
        return clean_text(opening_times)
    except Exception as e:
        print(f"Failed to get open hours for {url}: {e}")
        return ""
    finally:
        driver.quit()


class AttractionsSpider(scrapy.Spider):
    name = "attractions"
    start_index = 21
    max_index = 30

    def start_requests(self):
        url = "https://www.trip.com/restapi/soa2/19974/getTripAttractionList"
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.trip.com",
            "Referer": "https://www.trip.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Cookie": "ibulanguage=EN; cookiePricesDisplayed=USD; nfes_isSupportWebP=1; UBT_VID=1758073760791.054dalGNF1px; GUID=09034128116461760750; ...",
        }

        for i in range(self.start_index, self.max_index + 1):
            payload = {"cityId":0,"cityType":3,"count":10,"keyword":None,"pageId":"10650006153","districtId":434,"token":"MzYyNzI1OTAsMTA1NTg4NTgsOTQ3ODYsMjA5MDU2NDQsMTI5NzU3NTEwLDEwNTI0MTk0LDE0MzE1OTM5NCw3ODkyNywyODU3NTMwMyw3ODkyNg","index":i,"returnModuleType":"product","scene":"gsDestination","sortType":1,"traceId":None,"suggestRealName":"","userCoordinate":{},"excludePoiIdList":[],"extendMap":{"NEW_LIST_COMPONENT":"true"},"filter":{"filterItems":[],"coordinateFilter":{"coordinateType":"wgs84","latitude":0,"longitude":0},"itemType":""},"head":{"cid":"09034128116461760750","ctok":"","cver":"1.0","lang":"01","sid":"8888","syscode":"09","auth":"","xsid":"","extension":[{"name":"gs_incremental_cver","value":"undefined"},{"name":"source","value":"web"},{"name":"technology","value":"H5"},{"name":"os","value":"Online"},{"name":"platform","value":"Online"},{"name":"application","value":""},{"name":"locale","value":"en-US"},{"name":"currency","value":"USD"},{"name":"componentVersion","value":"0.2.14-beta.2"}],"Locale":"en-US","Language":"en","Currency":"USD","ClientID":"09034128116461760750"}}

            yield scrapy.Request(
                url,
                method="POST",
                headers=headers,
                body=json.dumps(payload),
                callback=self.parse,
            )

    def parse(self, response):
        data = response.json()
        attractions = data.get("attractionList", [])
        for item in attractions:
            card = item.get("card", {})
            
            # Lấy object coordinate một cách an toàn
            coordinate_info = card.get("coordinate", {})
            if coordinate_info is None:
                coordinate_info = {}

            meta = {
                "name": card.get("poiName"),
                "img": card.get("coverImageUrl", ""),
                "rating": card.get("commentInfo", {}).get("commentScore", 0),
                "review_count": card.get("commentInfo", {}).get("commentCount", 0),
                "price": card.get("priceInfo", {}).get("price", 0),
                "short_desc": clean_text(card.get("commentInfo", {}).get("commentContent", ""), mode="remove"),
                "long_desc": clean_text(card.get("introduction", ""), mode="remove"),
                "url": card.get("detailUrl"),
                
                # ===== PHẦN THÊM VÀO =====
                "latitude": coordinate_info.get("latitude"),
                "longitude": coordinate_info.get("longitude"),
                # =========================
            }
            # gọi sang trang detail để lấy thêm address + open_hours
            if meta["url"]:
                yield response.follow(meta["url"], callback=self.parse_detail, cb_kwargs={"meta": meta})
                
    def parse_detail(self, response, meta):
        # scrape address bằng Scrapy
        address = response.css(".one-line .field::text").getall() 
        address = address[2].strip() if len(address) > 2 else None

        meta["address"] = clean_text(address)

        # dùng Selenium để lấy open_hours
        meta["open_hours"] = get_open_hours(response.url)

        yield meta