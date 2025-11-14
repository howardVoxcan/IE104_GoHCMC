import os
import csv
import json
import requests
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# ===== 1️⃣ Load môi trường =====
load_dotenv()

# ===== 2️⃣ Cấu hình Cloudinary =====
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ===== 3️⃣ Hàm tải và upload ảnh =====
def download_and_upload_image(image_url, code, folder="images"):
    """Tải ảnh từ URL và upload lên Cloudinary"""
    try:
        os.makedirs(folder, exist_ok=True)
        local_path = os.path.join(folder, f"{code}.jpg")

        # Download ảnh
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(resp.content)

        # Upload lên Cloudinary
        upload_result = cloudinary.uploader.upload(local_path, public_id=code)
        cloud_url = upload_result.get("secure_url")
        return cloud_url
    except Exception as e:
        print(f"⚠️ Lỗi tải hoặc upload ảnh ({code}): {e}")
        return None

# ===== 4️⃣ Quy trình chính =====
def process_images(
    input_csv="attractions_normalized.csv",
    output_csv="attractions_with_images.csv",
    output_json="uploaded_images.json"
):
    """Đọc CSV, tải ảnh và upload lên Cloudinary, thêm cột image_url"""
    print(f"🚀 Bắt đầu xử lý file: {input_csv}")

    # Thử đọc CSV với nhiều bảng mã khác nhau
    encodings_to_try = ["utf-8-sig", "cp1258", "latin1"]
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(input_csv, encoding=enc)
            print(f"✅ Đọc file thành công với encoding: {enc}")
            break
        except UnicodeDecodeError:
            print(f"⚠️ Lỗi giải mã với encoding: {enc}, thử loại khác...")
    else:
        raise ValueError("❌ Không thể đọc được file CSV với các bảng mã thông dụng.")

    if "image_path" not in df.columns or "CODE" not in df.columns:
        raise ValueError("❌ File CSV cần có cột 'image_path' và 'CODE'.")

    if "image_url" not in df.columns:
        df["image_url"] = ""

    image_data = []
    success_count = 0
    total_count = len(df)

    for i, row in tqdm(df.iterrows(), total=total_count, desc="📸 Upload ảnh"):
        img_url = str(row.get("image_path", "")).strip()
        code = str(row.get("CODE", "")).strip()

        if not img_url or not code:
            continue

        # Nếu đã có link cloudinary, bỏ qua
        if pd.notna(row.get("image_url")) and str(row["image_url"]).startswith("https://res.cloudinary.com"):
            continue

        cloud_url = download_and_upload_image(img_url, code)
        if cloud_url:
            df.at[i, "image_url"] = cloud_url
            success_count += 1
            image_data.append({
                "CODE": code,
                "original_path": img_url,
                "cloud_url": cloud_url
            })

    # ===== Ghi file CSV có thêm cột image_url =====
    df.to_csv(output_csv, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_NONNUMERIC)

    # ===== Ghi file JSON kết quả =====
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(image_data, f, indent=4, ensure_ascii=False)

    print("\n📊 ====== TỔNG KẾT ======")
    print(f"🔹 Tổng số dòng trong CSV: {total_count}")
    print(f"✅ Upload thành công: {success_count}")
    print(f"💾 CSV kết quả: {output_csv}")
    print(f"💾 JSON danh sách ảnh: {output_json}")

# ===== Run =====
if __name__ == "__main__":
    process_images()
