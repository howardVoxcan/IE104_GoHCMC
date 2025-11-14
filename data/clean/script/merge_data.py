import pandas as pd

# Danh sách các file cần merge
files = ['base_data.csv', 'hotels.csv', 'restaurants.csv', 'attractions.csv']  # thay bằng tên file thực tế

merged_df = pd.DataFrame()
total_rows = 0
error_files = []

for f in files:
    try:
        df = pd.read_csv(f)
        rows_before = len(df)
        merged_df = pd.concat([merged_df, df], ignore_index=True)
        total_rows += rows_before
        print(f"[OK] Đã đọc file '{f}' với {rows_before} dòng.")
    except Exception as e:
        print(f"[ERROR] Không thể đọc file '{f}': {e}")
        error_files.append(f)

# Xuất file CSV cuối cùng
try:
    merged_df.to_csv('merged_output.csv', index=False, encoding='utf-8-sig')
    print(f"\n[DONE] Đã merge xong tất cả file vào 'merged_data.csv'.")
    print(f"Tổng số dòng đã merge: {len(merged_df)}")
    if error_files:
        print(f"Những file bị lỗi không đọc được: {error_files}")
except Exception as e:
    print(f"[ERROR] Lỗi khi lưu file: {e}")
