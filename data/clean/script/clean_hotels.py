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

# ========== 1️⃣ Load môi trường ==========
load_dotenv()

# ========== 2️⃣ Cấu hình API ==========
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in environment/.env")

client = genai.Client(api_key=GEMINI_KEY)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ========== 3️⃣ Hàm gọi Gemini ==========
def call_gemini_prompt(prompt, preferred_models=None):
    if preferred_models is None:
        preferred_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for model_name in preferred_models:
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt)
            if hasattr(resp, "text") and resp.text:
                return resp.text.strip()
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            continue
    return None

# ========== 4️⃣ Chuẩn hóa LOCATION ==========
def normalize_location(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+", "", text)
    text = unidecode.unidecode(text)
    return text.strip()

# ========== 5️⃣ Sinh mã CODE bắt đầu từ AC012 ==========
def generate_code(index):
    return f"AC{index + 12:03d}"

# ========== 6️⃣ Random RATING (MAX = 5) ==========
def randomize_rating(df, column_name="RATING (MAX = 5)"):
    if column_name not in df.columns:
        print(f"⚠️ Không tìm thấy cột '{column_name}', sẽ thêm mới.")
        df[column_name] = 0

    zero_before = (df[column_name] == 0).sum() + df[column_name].isna().sum()
    print(f"🔍 Trước khi sửa: {zero_before} giá trị 0 hoặc NaN trong cột '{column_name}'")

    df[column_name] = df[column_name].apply(
        lambda x: round(random.uniform(3.5, 5.0), 1) if pd.isna(x) or x == 0 else x
    )

    zero_after = (df[column_name] == 0).sum() + df[column_name].isna().sum()
    print(f"✅ Sau khi sửa: {zero_after} giá trị 0 hoặc NaN còn lại trong cột '{column_name}'")

    return df

# ========== 7️⃣ Gọi Gemini để điền địa chỉ ==========
def fetch_address(location):
    prompt = f"Provide the full English postal address (one line) for the place named '{location}'. If unknown, answer 'Address unknown'."
    return call_gemini_prompt(prompt)

# ========== 8️⃣ Sinh mô tả ngắn ==========
def generate_description(name, long_desc):
    if long_desc and isinstance(long_desc, str) and long_desc.strip():
        prompt = f"Summarize in one short English sentence: {long_desc}"
    else:
        prompt = f"Write one short English sentence describing the place named '{name}'."
    desc = call_gemini_prompt(prompt)
    if desc:
        return re.split(r"[.!?]\\s+", desc.strip())[0].strip()
    return None

# ========== 9️⃣ Tải & upload ảnh lên Cloudinary ==========
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

# ========== 🔟 Quy trình chính ==========
def normalize_data(input_csv="hotels.csv", output_csv="hotels_normalized.csv"):
    df = pd.read_csv(input_csv)

    # Chuẩn hóa LOCATION
    df["LOCATION"] = df["LOCATION"].apply(normalize_location)
    df["CODE"] = [generate_code(i) for i in range(len(df))]
    df["TYPE"] = "Accommodation"

    # Random rating hoàn chỉnh
    df = randomize_rating(df, column_name="RATING (MAX = 5)")

    tqdm.pandas(desc="Processing rows")

    for i, row in tqdm(df.iterrows(), total=len(df), desc="Normalizing"):
        # Address
        if "Address" in df.columns and (pd.isna(row["Address"]) or not str(row["Address"]).strip()):
            addr = fetch_address(row["LOCATION"])
            df.at[i, "Address"] = addr

        # Description
        if "Description" in df.columns and (pd.isna(row["Description"]) or not str(row["Description"]).strip()):
            desc = generate_description(row["LOCATION"], row.get("Long Description", ""))
            df.at[i, "Description"] = desc

        # Image upload
        if "image_path" in df.columns and pd.notna(row["image_path"]):
            img_url = download_and_upload_image(row["image_path"], row["CODE"])
            if img_url:
                df.at[i, "image_url"] = img_url

    # Ghi kết quả
    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_NONNUMERIC)

    # Xuất JSON ảnh
    image_data = [
        {"code": row["CODE"], "original": row["image_path"], "cloud_url": row.get("image_url", None)}
        for _, row in df.iterrows()
    ]
    with open("images_to_cloudinary.json", "w", encoding="utf-8") as f:
        json.dump(image_data, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Done! Saved to {output_csv} and images_to_cloudinary.json")

# ========== 1️⃣1️⃣ Run ==========
if __name__ == "__main__":
    normalize_data()
