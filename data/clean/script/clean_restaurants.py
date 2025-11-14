import os
import re
import csv
import json
import random
import requests
import pandas as pd
import unidecode
from tqdm import tqdm
from dotenv import load_dotenv
from google import genai
import cloudinary
import cloudinary.uploader
import time

# ===== 1️⃣ Load môi trường =====
load_dotenv()

# ===== 2️⃣ Cấu hình API =====
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in environment/.env")

client = genai.Client(api_key=GEMINI_KEY)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ===== 3️⃣ Hàm gọi Gemini batch =====
def call_gemini_batch_prompt(locations):
    """
    Gộp nhiều LOCATION vào 1 prompt, yêu cầu Gemini trả kết quả JSON gồm:
    { 'location': {'Address':..., 'Description':..., 'Long Description':...}, ... }
    """
    prompt = (
        "You are a helpful assistant that generates English information for multiple restaurant locations.\n"
        "For each location, provide the following fields:\n"
        "1. Address: The full English postal address (1 line)\n"
        "2. Description: One short English sentence summarizing the place\n"
        "3. Long Description: A 2-3 sentence English description about the place and its atmosphere.\n"
        "Return the result as a JSON object where each key is the location name.\n"
        f"Locations: {json.dumps(locations)}"
    )
    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        if hasattr(resp, "text"):
            text = resp.text.strip()
        else:
            text = str(resp)

        # Lọc đoạn JSON từ phản hồi
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            result_json = match.group(0)
            return json.loads(result_json)
        else:
            print("⚠️ Gemini did not return valid JSON.")
            return {}
    except Exception as e:
        print("⚠️ Gemini batch error:", e)
        return {}

# ===== 4️⃣ Các hàm tiện ích =====
def normalize_location(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+", "", text)
    text = unidecode.unidecode(text)
    return text.strip()

def generate_code(index):
    return f"FB{index + 19:03d}"

def randomize_rating(df, column_name="RATING (MAX = 5)"):
    if column_name not in df.columns:
        print(f"⚠️ Không tìm thấy cột '{column_name}', sẽ thêm mới.")
        df[column_name] = 0
    zero_before = (df[column_name] == 0).sum() + df[column_name].isna().sum()
    df[column_name] = df[column_name].apply(
        lambda x: round(random.uniform(3.5, 5.0), 1) if pd.isna(x) or x == 0 else x
    )
    zero_after = (df[column_name] == 0).sum() + df[column_name].isna().sum()
    updated = zero_before - zero_after
    print(f"✅ Đã cập nhật {updated} giá trị rating trống hoặc = 0.")
    return df, updated

def download_and_upload_image(image_url, code):
    try:
        img_data = requests.get(image_url, timeout=10).content
        os.makedirs("images", exist_ok=True)
        local_path = f"images/{code}.jpg"
        with open(local_path, "wb") as f:
            f.write(img_data)
        upload_result = cloudinary.uploader.upload(local_path, public_id=code)
        return upload_result.get("secure_url")
    except Exception as e:
        print(f"⚠️ Image error ({code}):", e)
        return None

# ===== 5️⃣ Quy trình chính =====
def normalize_data(input_csv="base_data.csv", output_csv="restaurants_normalized.csv", batch_size=10):
    print(f"🚀 Bắt đầu xử lý file: {input_csv}")
    df = pd.read_csv(input_csv)
    original_count = len(df)

    # Xóa LOCATION trống
    df = df[df["LOCATION"].notna() & (df["LOCATION"].astype(str).str.strip() != "")]
    removed_rows = original_count - len(df)
    if removed_rows > 0:
        print(f"🗑️ Đã xóa {removed_rows} dòng có LOCATION trống.")

    # Chuẩn hóa LOCATION
    df["LOCATION"] = df["LOCATION"].apply(normalize_location)

    # Gán CODE & TYPE
    df["CODE"] = [generate_code(i) for i in range(len(df))]
    df["TYPE"] = "F&B"

    # Random rating
    df, updated_ratings = randomize_rating(df, column_name="RATING (MAX = 5)")

    # Lấy danh sách địa điểm cần bổ sung thông tin
    locations_to_fill = []
    for _, row in df.iterrows():
        if any([
            pd.isna(row.get("Address")),
            pd.isna(row.get("Description")),
            pd.isna(row.get("Long Description")),
            not str(row.get("Address", "")).strip(),
            not str(row.get("Description", "")).strip(),
            not str(row.get("Long Description", "")).strip()
        ]):
            locations_to_fill.append(row["LOCATION"])

    print(f"📍 Có {len(locations_to_fill)} địa điểm cần gọi Gemini để bổ sung thông tin.")

    # Chia batch để giảm quota
    total_batches = (len(locations_to_fill) + batch_size - 1) // batch_size
    for b in range(total_batches):
        batch = locations_to_fill[b * batch_size : (b + 1) * batch_size]
        print(f"⚙️ Gọi Gemini cho batch {b+1}/{total_batches} ({len(batch)} địa điểm)...")
        result = call_gemini_batch_prompt(batch)
        time.sleep(2)  # tránh spam quá nhanh

        # Ghi kết quả vào dataframe
        for loc, info in result.items():
            mask = df["LOCATION"] == loc
            if not any(mask):
                continue
            if isinstance(info, dict):
                df.loc[mask, "Address"] = info.get("Address", "Address unknown")
                df.loc[mask, "Description"] = info.get("Description", "")
                df.loc[mask, "Long Description"] = info.get("Long Description", "")

    # Upload ảnh
    uploaded_count = 0
    total_images = 0
    for i, row in tqdm(df.iterrows(), total=len(df), desc="📸 Upload ảnh"):
        if "image_path" in df.columns and pd.notna(row["image_path"]) and str(row["image_path"]).strip():
            total_images += 1
            img_url = download_and_upload_image(row["image_path"], row["CODE"])
            if img_url:
                uploaded_count += 1
                df.at[i, "image_url"] = img_url

    # Ghi kết quả
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_NONNUMERIC)

    # Xuất JSON ảnh
    image_data = [
        {"code": row["CODE"], "original": row.get("image_path"), "cloud_url": row.get("image_url")}
        for _, row in df.iterrows()
        if "image_path" in df.columns
    ]
    with open("images_to_cloudinary.json", "w", encoding="utf-8") as f:
        json.dump(image_data, f, indent=4, ensure_ascii=False)

    # Log tổng kết
    print("\n📊 ====== TỔNG KẾT ======")
    print(f"🔹 Tổng số dòng ban đầu: {original_count}")
    print(f"🔹 Số dòng bị xóa (LOCATION trống): {removed_rows}")
    print(f"🔹 Số dòng còn lại sau xử lý: {len(df)}")
    print(f"⭐ Số rating được cập nhật: {updated_ratings}")
    print(f"🖼️ Tổng số ảnh tải về: {total_images}")
    print(f"☁️ Ảnh upload Cloudinary thành công: {uploaded_count}")
    print(f"💾 Dữ liệu đã lưu tại: {output_csv}")
    print(f"💾 Danh sách ảnh lưu tại: images_to_cloudinary.json")

# ===== Run =====
if __name__ == "__main__":
    normalize_data()
