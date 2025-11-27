import csv
import json
import os

# --- 1. Tải locations từ CSV (Giữ nguyên) ---
filename = "data/clean/data.csv"
locations = []

try:
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            location = row['LOCATION'].strip()
            locations.append(location)
except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file CSV tại: {filename}")
    print("Vui lòng kiểm tra lại đường dẫn. Sử dụng vài location mẫu...")
    locations = ["Hà Nội", "Đà Nẵng", "TP. Hồ Chí Minh", "Hội An", "Sa Pa"]

print(f"Đã tải {len(locations)} locations.")

# --- 2. Templates (Giữ nguyên) ---
start_templates = [
    "Start from {}", "Begin at {}", "My first stop is {}",
    "The trip starts at {}", "I want to start at {}"
]
end_templates = [
    "End at {}", "Finish at {}", "My last stop is {}",
    "The trip ends at {}", "I want to end at {}"
]

# --- 3. Function generate userSays (Giữ nguyên) ---
def generate_user_says(locations, templates):
    user_says = []
    # Lấy MỌI location, không sample
    for template in templates:
        prefix, suffix = template.split('{}')
        for loc in locations:
            user_says.append({
                "isTemplate": False,
                "count": 0,
                "updated": None,
                "data": [
                    {"text": prefix, "userDefined": False},
                    {
                        "text": loc,
                        "alias": "locations", # Phải khớp với 'name' của parameter
                        "meta": "@locations",
                        "userDefined": True
                    },
                    {"text": suffix, "userDefined": False}
                ],
                "id": ""
            })
    return user_says

# --- 4. Function tạo Intent DẠNG GỘP (SỬA ĐỔI) ---
# Function này tạo ra 1 file JSON duy nhất, chứa cả userSays
def create_combined_intent(intent_name, reply_text, user_says_data):
    return {
        "name": intent_name,
        "auto": True,
        "responses": [
            {
                "messages": [
                    {
                        "type": "message",
                        "condition": "",
                        "speech": [reply_text]
                    }
                ],
                "parameters": [
                    {
                        "name": "locations", # Phải khớp với 'alias'
                        "dataType": "@locations",
                        "value": "$locations",
                        "isList": False # Đúng: Start/End chỉ có 1
                    }
                ]
            }
        ],
        "userSays": user_says_data # <-- Quan trọng: Nhúng userSays vào đây
    }

# --- 5. Logic tạo và lưu file (SỬA ĐỔI) ---

# Thư mục output cho các file JSON đơn lẻ
output_dir = "dialogflow/dialogflow_chatbot/json_for_upload" 
os.makedirs(output_dir, exist_ok=True)

# 1. Tạo dữ liệu userSays
print("Generating userSays for start.location...")
start_user_says = generate_user_says(locations, start_templates)
print("Generating userSays for end.location...")
end_user_says = generate_user_says(locations, end_templates)

# 2. Tạo intent (dạng gộp)
start_intent = create_combined_intent(
    "set.start.location", 
    "Got it. I’ve set the starting location.",
    start_user_says
)
end_intent = create_combined_intent(
    "set.end.location", 
    "Alright. I’ve set the ending location.",
    end_user_says
)

# 3. Lưu file
print(f"Saving set.start.location.json...")
with open(os.path.join(output_dir, "set.start.location.json"), "w", encoding="utf-8") as f:
    json.dump(start_intent, f, indent=2, ensure_ascii=False)

print(f"Saving set.end.location.json...")
with open(os.path.join(output_dir, "set.end.location.json"), "w", encoding="utf-8") as f:
    json.dump(end_intent, f, indent=2, ensure_ascii=False)

print("---")
print(f"Hoàn tất! Đã tạo 2 file JSON (dạng gộp) trong thư mục: {output_dir}")
print("Bạn có thể dùng nút 'Upload Intent' cho 2 file này.")