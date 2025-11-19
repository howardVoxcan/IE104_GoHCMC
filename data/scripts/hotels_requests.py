import requests
import json
import time
from datetime import datetime, timedelta

def get_formatted_date(offset_days=0):
    date = datetime.now() + timedelta(days=offset_days)
    return date.strftime("%Y%m%d")

check_in = get_formatted_date(0)
check_out = get_formatted_date(1)


url = "https://www.trip.com/htls/getHotelListDynamicRefresh"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.trip.com",
    "Referer": "https://www.trip.com/hotels/list?city=301"
}

# Đây là payload base — copy từ Network tab
base_payload = {
    "guideLogin": "T",
    "search": {
        "sessionId": "191cfd71-439b-0eb5-ccce-a5d403df3b3b",
        "preHotelCount": 0,
        "preHotelIds": [],
        "checkIn": f"{check_in}",
        "checkOut": f"{check_out}",
        "filters": [
            {"filterId": "29|1", "value": "1|2", "type": "29"},
            {"filterId": "17|1", "type": "17", "value": "1", "subType": "2"},
            {"filterId": "80|0|1", "type": "80", "value": "0", "subType": "2"}
        ],
        "pageCode": 10320668148,
        "location": {
            "geo": {
                "countryID": 0,
                "provinceID": 0,
                "cityID": 301,
                "districtID": 0,
                "oversea": True
            },
            "coordinates": []
        },
        "pageIndex": 1,
        "pageSize": 20,  # mỗi page lấy 20 khách sạn
        "roomQuantity": 1,
        "hotelIds": [],
        "lat": 10.805785,
        "lng": 106.665339
    },
    "batchRefresh": {"batchId": "", "batchSeqNo": 0},
    "queryTag": "NORMAL",
    "mapType": "GOOGLE",
    "extends": {
        "enableDynamicRefresh": "T",
        "isFirstDynamicRefresh": "T",
        "NeedHotelHighLight": "T",
        "needEntireSetRoomDesc": "T"
    },
    "tokenList": [
        "eJyrVkrJLC7ISawMKMpMTlWyMjHSUcpNLC5JLfLIL0nN8UxRsjKxMDMxNTY01FHKSSwuCS1ISSxJDcnMTVWyMjQ3tTA0MDU2MjYxNKoFAKxTFy8="
    ],
    "head": {
        "platform": "PC",
        "clientId": "1757482530872.a128dBt1UOZA",
        "bu": "ibu",
        "group": "TRIP",
        "aid": "6334952",
        "sid": "202570250",
        "ouid": "ctag.hash.2zjvmdgxx5qw",
        "region": "XX",
        "locale": "en-XX",
        "currency": "USD",
        "deviceID": "PC",
        "href": "https://www.trip.com/hotels/list?city=301"
    }
}

all_hotels = []

# loop nhiều trang
for page in range(1, 26): 
    payload = json.loads(json.dumps(base_payload))  # clone dict
    payload["search"]["pageIndex"] = page

    res = requests.post(url, headers=headers, json=payload)
    data = res.json()

    hotels = data.get("hotelList", [])
    print(f"Trang {page}: {len(hotels)} khách sạn")

    if not hotels:
        break

    all_hotels.extend(hotels)
    time.sleep(1)  # tránh spam

print(f"Tổng cộng lấy được {len(all_hotels)} khách sạn")

# Lưu ra file JSON
with open("hotels.json", "w", encoding="utf-8") as f:
    json.dump(all_hotels, f, ensure_ascii=False, indent=2)
