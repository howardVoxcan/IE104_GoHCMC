import os
import re
import json
import time
import difflib
import pandas as pd
import unidecode
from tqdm import tqdm
from dotenv import load_dotenv
from google import genai

# ===== 1️⃣ Load môi trường =====
load_dotenv(override=True)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in environment/.env")

client = genai.Client(api_key=GEMINI_KEY)

CACHE_FILE = "cache_restaurants.json"
RAW_LOG = "gemini_raw_responses.log"

# ===== 2️⃣ Tiện ích =====
def normalize(text):
    if not isinstance(text, str):
        return ""
    t = unidecode.unidecode(text.lower())
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def clean_field(value):
    """Chuyển các giá trị nan, None, null về chuỗi rỗng"""
    if not isinstance(value, str):
        value = str(value)
    v = value.strip()
    if v.lower() in ["nan", "none", "null", ""]:
        return ""
    return v

def load_cache():
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def save_raw_response(raw_text):
    with open(RAW_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        f.write(raw_text if isinstance(raw_text, str) else str(raw_text))

# ===== 3️⃣ Gọi Gemini =====
def call_gemini_fill_missing(batch_requests):
    """Gọi Gemini để sinh phần còn thiếu"""
    if not batch_requests:
        print("⚠️ Không có dữ liệu để gửi Gemini.")
        return {}

    prompt = (
        "You are a helpful assistant that fills missing English info for restaurants in Ho Chi Minh City, Vietnam.\n"
        "For each restaurant provided, only generate the missing fields among: Address, Description, Long Description.\n"
        "- Address: Full English postal address (1 line, located in Ho Chi Minh City, Vietnam)\n"
        "- Description: One short English sentence summarizing the restaurant.\n"
        "- Long Description: 4–5 English sentences describing the restaurant, food, and atmosphere.\n\n"
        "Return ONLY valid JSON, with restaurant name as key.\n\n"
        f"Data: {json.dumps(batch_requests, ensure_ascii=False)}"
    )

    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        # --- Đọc text phản hồi ---
        text = None
        try:
            if hasattr(resp, "candidates") and resp.candidates:
                text = resp.candidates[0].content.parts[0].text
            elif hasattr(resp, "text") and resp.text:
                text = resp.text
        except Exception as e:
            print("⚠️ Không thể đọc nội dung từ phản hồi Gemini:", e)

        if not text:
            print("⚠️ Gemini không trả dữ liệu.")
            save_raw_response(str(resp))
            return {}

        save_raw_response(text)
        print("🧾 Gemini raw sample:", text[:200].replace("\n", " "), "...")

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print("⚠️ Không tìm thấy JSON trong phản hồi Gemini.")
            return {}

        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict) or not parsed:
            print("⚠️ Gemini trả về JSON rỗng hoặc không hợp lệ.")
            return {}

        print(f"✅ Nhận được {len(parsed)} mục từ Gemini.")
        return parsed

    except Exception as e:
        print("❌ Lỗi khi gọi Gemini:", e)
        return {}

# ===== 4️⃣ Quy trình chính =====
def generate_restaurant_info(
    input_csv="restaurants.csv",
    output_csv="restaurants_with_info.csv",
    batch_size=8,
    similarity_thresh=0.6
):
    print(f"🚀 Bắt đầu xử lý file: {input_csv}")

    encodings = ["utf-8-sig", "cp1258", "latin1"]
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(input_csv, encoding=enc)
            print(f"✅ Đọc CSV với encoding: {enc}")
            break
        except Exception as e:
            print(f"⚠️ Lỗi đọc với {enc}: {e}")
    if df is None:
        raise ValueError("❌ Không thể đọc file CSV.")

    if "LOCATION" not in df.columns:
        raise ValueError("❌ File CSV phải có cột LOCATION.")

    df["LOCATION"] = df["LOCATION"].astype(str)
    df["norm_loc"] = df["LOCATION"].apply(normalize)

    cache = load_cache()
    normalized_cache = {normalize(k): v for k, v in cache.items()}
    cache = normalized_cache

    norm_list = df["norm_loc"].tolist()
    requests = []

    # Tạo danh sách gửi Gemini
    for _, row in df.iterrows():
        n = row["norm_loc"]
        cached = cache.get(n, {})
        address = clean_field(row.get("Address", "")) or cached.get("Address", "")
        desc = clean_field(row.get("Description", "")) or cached.get("Description", "")
        longdesc = clean_field(row.get("Long Description", "")) or cached.get("Long Description", "")

        missing_fields = []
        if not address:
            missing_fields.append("Address")
        if not desc:
            missing_fields.append("Description")
        if not longdesc:
            missing_fields.append("Long Description")

        # Chỉ gửi nếu có ít nhất 1 trường thiếu
        if missing_fields:
            requests.append({
                "name": row["LOCATION"],
                "Address": address,
                "Description": desc,
                "Long Description": longdesc,
            })
        else:
            cache[n] = {"Address": address, "Description": desc, "Long Description": longdesc}

    print(f"📍 Có {len(requests)} địa điểm cần bổ sung thông tin bằng Gemini.")

    # Gọi Gemini theo batch
    total_batches = (len(requests) + batch_size - 1) // batch_size
    for b in range(total_batches):
        batch = requests[b * batch_size:(b + 1) * batch_size]
        print(f"🧠 Gọi Gemini batch {b+1}/{total_batches} ({len(batch)} địa điểm)...")
        result = call_gemini_fill_missing(batch)
        time.sleep(1.5)

        for returned_name, fields in result.items():
            if not isinstance(fields, dict):
                continue
            rnorm = normalize(returned_name)
            target_norm = None
            if rnorm in cache:
                target_norm = rnorm
            else:
                matches = difflib.get_close_matches(rnorm, norm_list, n=1, cutoff=similarity_thresh)
                target_norm = matches[0] if matches else rnorm

            existing = cache.get(target_norm, {})
            merged = {
                "Address": fields.get("Address", existing.get("Address", "")),
                "Description": fields.get("Description", existing.get("Description", "")),
                "Long Description": fields.get("Long Description", existing.get("Long Description", "")),
            }
            cache[target_norm] = merged
        save_cache(cache)

    # Ghi kết quả
    def get_cached(n, k):
        return cache.get(n, {}).get(k, "")

    df["Address"] = df["norm_loc"].apply(lambda n: get_cached(n, "Address"))
    df["Description"] = df["norm_loc"].apply(lambda n: get_cached(n, "Description"))
    df["Long Description"] = df["norm_loc"].apply(lambda n: get_cached(n, "Long Description"))

    df.drop(columns=["norm_loc"], inplace=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig", quoting=1)

    print("\n✅ Hoàn tất!")
    print(f"💾 File kết quả: {output_csv}")
    print(f"🧠 Cache: {CACHE_FILE}")
    print(f"📝 Log phản hồi: {RAW_LOG}")

# ===== 5️⃣ Chạy =====
if __name__ == "__main__":
    generate_restaurant_info()
