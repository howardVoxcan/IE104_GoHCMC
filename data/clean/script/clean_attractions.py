import os
import re
import csv
import json
import random
import pandas as pd
import unidecode
import time
from tqdm import tqdm
from dotenv import load_dotenv
from google import genai

# ===== 1️⃣ Load môi trường =====
load_dotenv()

# ===== 2️⃣ Cấu hình API =====
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in environment/.env")

client = genai.Client(api_key=GEMINI_KEY)
CACHE_FILE = "cache_attractions.json"

# ===== 3️⃣ Cache =====
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

# ===== 4️⃣ Gọi Gemini hợp nhất =====
def call_gemini_for_locations(locations):
    """
    Gọi Gemini để sinh đồng thời TYPE + Address + Description + Long Description
    Yêu cầu:
    - Address phải nằm trong Ho Chi Minh City, Vietnam
    - Nếu có nhiều address khác nhau, chỉ lấy 1 cái duy nhất
    - Long Description dài 4–5 câu, mô tả chi tiết về LOCATION
    """
    prompt = (
        "You are a helpful assistant that classifies and describes tourist attractions in Ho Chi Minh City, Vietnam.\n"
        "For each location provided, return a JSON object where each key is the location name, "
        "and each value is an object with the following fields:\n"
        "1. TYPE: One of [Market, Transportation, Local, Entertainment], following these rules:\n"
        "   - Market: shopping malls or markets\n"
        "   - Transportation: stations, bus stops, train or metro stations\n"
        "   - Local: temples, shrines, or historical architecture\n"
        "   - Entertainment: all other leisure or tourist places\n"
        "2. Address: Full English postal address located in Ho Chi Minh City, Vietnam. "
        "If multiple addresses exist, choose only one valid address in Ho Chi Minh City.\n"
        "3. Description: One short English sentence summarizing the place.\n"
        "4. Long Description: 4–5 English sentences describing the location in detail, its features, and atmosphere.\n\n"
        "Return the result strictly as JSON. Example:\n"
        "{ 'Ben Thanh Market': {'TYPE':'Market','Address':'Ben Thanh, District 1, Ho Chi Minh City, Vietnam','Description':'...','Long Description':'...'}, ... }\n\n"
        f"Locations: {json.dumps(locations)}"
    )
    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = getattr(resp, "text", str(resp)).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            print("⚠️ Gemini did not return valid JSON.")
            return {}
    except Exception as e:
        print("⚠️ Gemini combined error:", e)
        return {}

# ===== 5️⃣ Tiện ích =====
def normalize_location(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+", "", text)
    text = unidecode.unidecode(text)
    return text.strip()

def randomize_rating(df, column_name="RATING (MAX = 5)"):
    if column_name not in df.columns:
        print(f"⚠️ Không tìm thấy cột '{column_name}', sẽ thêm mới.")
        df[column_name] = 0
    df[column_name] = df[column_name].apply(
        lambda x: round(random.uniform(3.5, 5.0), 1) if pd.isna(x) or x == 0 else x
    )
    print("✅ Đã cập nhật rating ngẫu nhiên.")
    return df

# ===== 6️⃣ Sinh CODE tăng dần theo TYPE =====
def assign_code_by_type(df):
    type_start = {
        "Entertainment": 16,
        "Market": 9,
        "Transportation": 10,
        "Local": 13,
    }
    codes = []
    counters = type_start.copy()

    for _, row in df.iterrows():
        t = row["TYPE"]
        if t not in type_start:
            t = "Entertainment"

        prefix = {"Entertainment": "EN", "Market": "MA", "Transportation": "TP", "Local": "LC"}[t]
        codes.append(f"{prefix}{counters[t]:03d}")
        counters[t] += 1  # tăng liên tục cho TYPE đó
    df["CODE"] = codes
    return df

# ===== 7️⃣ Quy trình chính =====
def normalize_data(input_csv="attractions.csv", output_csv="attractions_normalized.csv", batch_size=10):
    print(f"🚀 Bắt đầu xử lý file: {input_csv}")
    df = pd.read_csv(input_csv)
    original_count = len(df)

    # Xóa LOCATION trống
    df = df[df["LOCATION"].notna() & (df["LOCATION"].astype(str).str.strip() != "")]
    print(f"📍 Còn lại {len(df)} dòng sau khi loại bỏ LOCATION trống.")

    # Chuẩn hóa LOCATION
    df["LOCATION"] = df["LOCATION"].apply(normalize_location)

    # ===== Load cache =====
    cache = load_cache()
    all_locations = df["LOCATION"].tolist()
    new_locations = [loc for loc in all_locations if loc not in cache]

    print(f"💾 Cache hiện có {len(cache)} địa điểm.")
    if new_locations:
        print(f"⚙️ Gọi Gemini cho {len(new_locations)} địa điểm mới...")
        total_batches = (len(new_locations) + batch_size - 1) // batch_size
        for b in range(total_batches):
            batch = new_locations[b * batch_size : (b + 1) * batch_size]
            print(f"🧠 Batch {b+1}/{total_batches}: {len(batch)} địa điểm")
            result = call_gemini_for_locations(batch)
            cache.update(result)
            save_cache(cache)
            time.sleep(2)
        print("✅ Đã cập nhật cache_attractions.json")
    else:
        print("✅ Tất cả địa điểm đã có trong cache, không cần gọi Gemini.")

    # ===== Gán dữ liệu từ cache =====
    df["TYPE"] = df["LOCATION"].apply(lambda x: cache.get(x, {}).get("TYPE", "Entertainment"))
    df["Address"] = df["LOCATION"].apply(lambda x: cache.get(x, {}).get("Address", "Ho Chi Minh City, Vietnam"))
    df["Description"] = df["LOCATION"].apply(lambda x: cache.get(x, {}).get("Description", ""))
    df["Long Description"] = df["LOCATION"].apply(lambda x: cache.get(x, {}).get("Long Description", ""))

    # ===== Random rating =====
    df = randomize_rating(df)

    # ===== Gán CODE =====
    df = assign_code_by_type(df)

    # ===== Xuất file =====
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"\n💾 Đã lưu kết quả tại: {output_csv}")
    print(f"📊 Tổng {len(df)} địa điểm, đã sinh TYPE + mô tả + địa chỉ + CODE.")
    print(f"💡 Cache lưu tại: {CACHE_FILE}")

# ===== Run =====
if __name__ == "__main__":
    normalize_data()
