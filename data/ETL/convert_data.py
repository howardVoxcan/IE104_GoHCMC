import json
import csv
import re

def normalize_time(time_str):
    """
    Chuẩn hóa thời gian mở cửa theo định dạng:
    'Mon to Sun：_11:30-14:30 _17:30-21:30' → open_time = '11:30', close_time = '21:30'
    """
    if not time_str or time_str.strip() == "":
        return "0:00", "23:59"

    # Lấy tất cả mốc thời gian trong chuỗi
    times = re.findall(r"(\d{1,2}:\d{2})", time_str)
    if not times:
        return "0:00", "23:59"

    # open_time là mốc đầu tiên, close_time là mốc cuối cùng
    open_time = times[0]
    close_time = times[-1]
    return open_time, close_time


def convert_csv(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", newline="", encoding="utf-8") as outfile:
        reader = csv.DictReader(infile)
        
        fieldnames = [
            "CODE", "LOCATION", "TYPE", "RATING (MAX = 5)", "Address",
            "Description", "Long Description", "Tags_Creation_Description",
            "Ticket Info", "image_path", "open_time", "close_time", "coordinate", "tags"
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, row in enumerate(reader, start=1):
            code = None
            location = row.get("name", "").strip()
            rating = row.get("rating", "").strip()
            address = row.get("address", "").strip()
            short_desc = row.get("short_desc", "").strip()
            long_desc = row.get("long_desc", "").strip()
            img = row.get("img", "").strip()
            coordinate = row.get("latitude", "").strip() + ', ' + row.get("longitude", "").strip()
            price = row.get("price", "").strip()
            opening_times = row.get("opening_times", "").strip()

            open_time, close_time = normalize_time(opening_times)

            if location is None:
                continue

            new_row = {
                "CODE": code,
                "LOCATION": location,
                "TYPE": None,
                "RATING (MAX = 5)": rating,
                "Address": address,
                "Description": short_desc,
                "Long Description": long_desc,
                "Tags_Creation_Description": None,
                "Ticket Info": price,
                "image_path": img,
                "open_time": open_time,
                "close_time": close_time,
                "coordinate": coordinate,
                "tags": ""
            }

            writer.writerow(new_row)

    print(f"Đã chuyển đổi xong! File lưu tại: {output_file}")

def extract_field(data):
    """Trích xuất dữ liệu cần thiết từ JSON gốc"""
    basic = data.get("hotelBasicInfo", {})
    comment = data.get("commentInfo", {})
    position = data.get("positionInfo", {})
    room = data.get("roomInfo", {})
    tags = data.get("tags", [])
    feature_tags = [t.get("name", "") for t in tags if t.get("name")]

    # Lấy description ngắn và dài nếu có
    desc_short = basic.get("hotelEnName", "") + " located at " + basic.get("hotelAddress", "")
    desc_long = (
        f"{basic.get('hotelName', '')} is a {data.get('hotelStarInfo', {}).get('star', '')}-star hotel in "
        f"{position.get('cityName', '')}. Rated {comment.get('commentScore', '')}/"
        f"{comment.get('scoreMax', '')} by {comment.get('commenterNumber', '')}. "
        f"Guests praise its location near {position.get('positionDesc', '')}. "
        f"The most popular room is '{room.get('physicalRoomName', '')}' with {', '.join(room.get('bed', {}).get('contentList', []))}. "
        f"{' '.join([t for t in feature_tags])}"
    )

    # Tọa độ
    lat = position.get("coordinate", {}).get("lat")
    lng = position.get("coordinate", {}).get("lng")
    coordinate = f"{lat}, {lng}" if lat and lng else ""

    # Thời gian (mặc định hotel open 0:00 - 23:59)
    open_time, close_time = "0:00", "23:59"

    # Giá
    price = basic.get("price", "")
    ticket_info = f"~₫{float(price)*25000:.0f}/night (approx. ${price})" if price else ""

    return {
        "LOCATION": basic.get("hotelName", ""),
        "TYPE": None,
        "RATING (MAX = 5)": round(float(comment.get("commentScore", 0)) / 2, 1) if comment.get("commentScore") else "",
        "Address": basic.get("hotelAddress", ""),
        "Description": desc_short,
        "Long Description": desc_long,
        "Tags_Creation_Description": " | ".join(feature_tags),
        "Ticket Info": ticket_info,
        "image_path": basic.get("hotelImg", ""),
        "open_time": open_time,
        "close_time": close_time,
        "coordinate": coordinate,
        "tags": ", ".join(feature_tags)
    }

def convert_json(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    # Nếu file chứa 1 object chứ không phải list
    if isinstance(data_list, dict):
        data_list = [data_list]

    with open(output_file, "w", newline="", encoding="utf-8") as out:
        fieldnames = [
            "CODE", "LOCATION", "TYPE", "RATING (MAX = 5)", "Address",
            "Description", "Long Description", "Tags_Creation_Description",
            "Ticket Info", "image_path", "open_time", "close_time", "coordinate", "tags"
        ]
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for i, item in enumerate(data_list, start=1):
            row = extract_field(item)
            row["CODE"] = None
            writer.writerow(row)

    print(f"Đã chuyển đổi {len(data_list)} khách sạn → {output_file}")



if __name__ == "__main__":
    convert_csv("../data/raw/attractions.csv", "../data/clean/attractions.csv")
