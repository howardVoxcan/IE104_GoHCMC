import os
import csv
import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from ddgs import DDGS

# =========================
# Configuration
# =========================
CSV_FILE = "DATABASE-Sheet1.csv"
DOWNLOAD_DIR = "downloaded_images"
OUTPUT_JSON = "image_links.json"
SEARCH_IMAGE_COUNT = 1  # Chỉ tải 1 ảnh mỗi địa điểm

# =========================
# Load environment variables
# =========================
load_dotenv()

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Validate Cloudinary credentials
if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    raise ValueError(
        "Missing Cloudinary credentials. Please set CLOUDINARY_CLOUD_NAME, "
        "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in .env file"
    )

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# =========================
# Helper functions
# =========================

def create_download_dir():
    """Create download directory if it doesn't exist."""
    Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
    print(f"✓ Download directory: {DOWNLOAD_DIR}")


def search_and_download_image(location, code):
    """
    Search and download an image from DuckDuckGo (via ddgs).
    Có cơ chế random delay để tránh rate limit (403).
    """
    try:
        print(f"  🔍 Searching for: {location}")

        # Nghỉ ngẫu nhiên giữa các lần gọi để tránh bị chặn
        time.sleep(random.uniform(3, 6))

        with DDGS() as ddgs:
            results = ddgs.images(location, max_results=5)
            results = list(results)

        if not results:
            return False, None, "No image found via DuckDuckGo"

        # Chọn hình đầu tiên hợp lệ
        image_url = None
        for img in results:
            if img.get("image") and img["image"].startswith("http"):
                image_url = img["image"]
                break

        if not image_url:
            return False, None, "No valid image URL found"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()

        # Xác định phần mở rộng file
        content_type = response.headers.get("content-type", "")
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"

        local_filename = f"{code}{ext}"
        local_path = os.path.join(DOWNLOAD_DIR, local_filename)

        with open(local_path, "wb") as f:
            f.write(response.content)

        print(f"  ✓ Downloaded via DuckDuckGo (ddgs): {code}")
        return True, local_path, None

    except Exception as e:
        return False, None, f"DuckDuckGo (ddgs) search/download failed: {str(e)}"


def upload_to_cloudinary(local_path, code):
    """Upload image to Cloudinary."""
    try:
        result = cloudinary.uploader.upload(
            local_path,
            public_id=code,
            overwrite=True,
            folder="saigon_attractions"
        )
        url = result.get("secure_url")
        print(f"  ☁ Uploaded to Cloudinary: {code}")
        return True, url, None
    except Exception as e:
        return False, None, f"Upload failed: {str(e)}"


def process_csv():
    """Read CSV, download, upload, and collect image links."""
    image_links = {}
    failed_items = []

    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            items = list(reader)

        print(f"\n📊 Found {len(items)} items to process\n")

        for idx, row in enumerate(items, 1):
            code = row.get("CODE", "").strip()
            location = row.get("LOCATION", "").strip()

            if not code or not location:
                print(f"[{idx}/{len(items)}] ⚠ Skipping: Missing CODE or LOCATION")
                continue

            print(f"[{idx}/{len(items)}] Processing: {code}")

            # Step 1: Search & Download
            success, local_path, error = search_and_download_image(location, code)
            if not success:
                print(f"  ✗ {error}")
                failed_items.append({
                    "code": code,
                    "location": location,
                    "step": "search_download",
                    "error": error
                })
                continue

            # Step 2: Upload
            success, url, error = upload_to_cloudinary(local_path, code)
            if not success:
                print(f"  ✗ {error}")
                failed_items.append({
                    "code": code,
                    "location": location,
                    "step": "upload",
                    "error": error
                })
                continue

            # Step 3: Save URL
            image_links[code] = {
                "location": location,
                "url": url
            }

        return image_links, failed_items

    except FileNotFoundError:
        print(f"✗ CSV file not found: {CSV_FILE}")
        return {}, []


def save_json_output(image_links, failed_items):
    """Save all URLs & failed items to JSON."""
    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_items": len(image_links) + len(failed_items),
            "successful": len(image_links),
            "failed": len(failed_items),
            "cloudinary_folder": "saigon_attractions"
        },
        "images": image_links,
        "failed": failed_items
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Results saved to: {OUTPUT_JSON}")


def cleanup_local_images(keep_local=False):
    """Remove local files if not needed."""
    import shutil
    if not keep_local and os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
        print("✓ Cleaned up local images directory")

def main():
    """Main program"""
    print("=" * 70)
    print("📷 Image Download & Cloudinary Upload Tool (DuckDuckGo + ddgs)")
    print("=" * 70)

    create_download_dir()

    print(f"\n📥 Reading CSV file: {CSV_FILE}")
    image_links, failed_items = process_csv()

    print(f"\n💾 Saving results...")
    save_json_output(image_links, failed_items)

    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    print(f"Total Processed: {len(image_links) + len(failed_items)}")
    print(f"✓ Successful: {len(image_links)}")
    print(f"✗ Failed: {len(failed_items)}")

    if failed_items:
        print("\n⚠ Failed Items:")
        for item in failed_items:
            print(f"  - {item['code']} ({item['location']}): {item['error']}")

    # Clean up
    response = input("\nKeep local downloaded images? (y/n): ").lower()
    cleanup_local_images(keep_local=(response == 'y'))

    print("\n✓ Process completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
