import csv
import json
import random
import itertools
import os

# --- 1. Tải CSV (Giữ nguyên) ---
filename = "../../data_with_tags.csv"
locations = []

try:
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            location = row['LOCATION'].strip()
            locations.append(location)
except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file CSV tại: {filename}")
    locations = ["Hà Nội", "Đà Nẵng", "TP. Hồ Chí Minh", "Hội An", "Sa Pa"]

print(f"Đã tải {len(locations)} locations.")

# --- 2. Templates (Giữ nguyên) ---
add_templates = [
    "Add {}", "Can you add {}?", "I want to add {}", "Please include {}",
    "Put {} in my list", "Add {} and {}", "Please add both {} and {}",
    "Include {} and {} in my list", "I want to add {} as well as {}",
    "Add {} along with {}", "Put {} and {} in the list",
    "Could you add {} and also {}?",
]
remove_templates = [
    "Remove {}", "Can you remove {}?", "I want to remove {}", "Please delete {}",
    "Remove {} and {}", "Can you remove {} and {}?", "Please delete {} and {}",
    "I want to remove both {} and {}",
]

# --- 3. Function tạo UserSays (Giữ nguyên) ---
def generate_action_phrases(locations, templates):
    user_says = []
    entity_name = "locations"
    max_sample = min(len(locations), 50) 
    sample_size = max(1, int(max_sample * 0.2))
    sampled = random.sample(locations, min(len(locations), sample_size))
    paired = list(itertools.combinations(sampled, 2))[:max(1, sample_size // 2)]
    
    for template in templates:
        placeholder_count = template.count('{}')
        if placeholder_count == 2:
            for a, b in paired:
                parts = template.split('{}')
                if len(parts) == 3:
                    user_says.append({
                        "isTemplate": False, "count": 0, "updated": None,
                        "data": [
                            {"text": parts[0], "userDefined": False},
                            {"text": a, "alias": entity_name, "meta": f"@{entity_name}", "userDefined": True},
                            {"text": parts[1], "userDefined": False},
                            {"text": b, "alias": entity_name, "meta": f"@{entity_name}", "userDefined": True},
                            {"text": parts[2], "userDefined": False}
                        ], "id": ""
                    })
        elif placeholder_count == 1:
            for loc in sampled:
                parts = template.split('{}')
                if len(parts) == 2:
                    user_says.append({
                        "isTemplate": False, "count": 0, "updated": None,
                        "data": [
                            {"text": parts[0], "userDefined": False},
                            {"text": loc, "alias": entity_name, "meta": f"@{entity_name}", "userDefined": True},
                            {"text": parts[1], "userDefined": False}
                        ], "id": ""
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
                        "name": "locations", # Tên parameter (đã sửa)
                        "dataType": "@locations",
                        "value": "$locations", # (đã sửa)
                        "isList": True 
                    }
                ]
            }
        ],
        "userSays": user_says_data # <-- Quan trọng: Nhúng userSays vào đây
    }

# --- 5. Logic tạo và lưu file (SỬA ĐỔI) ---

# Thư mục output cho các file JSON đơn lẻ
output_dir = "json_for_upload" # Đặt tên thư mục mới
os.makedirs(output_dir, exist_ok=True)

# Danh sách các intent cần tạo
intents_to_create = [
    {
        "name": "trip.create.add.location",
        "templates": add_templates,
        "reply": "Okay, I've added the location(s) to your trip."
    },
    {
        "name": "trip.create.remove.location",
        "templates": remove_templates,
        "reply": "Got it. I've removed the location(s) from your trip."
    },
    {
        "name": "favourite.add.location",
        "templates": add_templates,
        "reply": "Okay, I've added the location(s) to your favourites."
    },
    {
        "name": "favourite.remove.location",
        "templates": remove_templates,
        "reply": "Got it. I've removed the location(s) from your favourites."
    }
]

print("Đang tạo file JSON (dạng 1 file) để upload...")

# Vòng lặp để tạo 4 intent riêng biệt
for intent_config in intents_to_create:
    intent_name = intent_config["name"]
    print(f"Generating: {intent_name}.json")
    
    # 1. Tạo userSays
    user_says_data = generate_action_phrases(locations, intent_config["templates"])
    
    # 2. Tạo intent (dạng gộp)
    combined_intent = create_combined_intent(
        intent_name, 
        intent_config["reply"], 
        user_says_data
    )
    
    # 3. Lưu file JSON (chỉ 1 file cho mỗi intent)
    intent_filename = os.path.join(output_dir, f"{intent_name}.json")
    with open(intent_filename, "w", encoding="utf-8") as f:
        json.dump(combined_intent, f, indent=2, ensure_ascii=False)

print("---")
print(f"Hoàn tất! Tất cả 4 file JSON (dạng gộp) đã được tạo trong thư mục: {output_dir}")