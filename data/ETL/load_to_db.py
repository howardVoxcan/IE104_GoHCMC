import csv
import json
import mysql.connector
from mysql.connector import errorcode

# -----------------------------
# 1️⃣ Cấu hình kết nối Database
# -----------------------------
DB_CONFIG = {
    "user": "root",
    "password": "your_password",
    "host": "localhost",
    "database": "travel_db",
    "port": 3306
}

# -----------------------------
# 2️⃣ Hàm kết nối
# -----------------------------
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected to DB successfully!")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Sai username hoặc password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("❌ Database chưa tồn tại.")
        else:
            print(err)
        return None

# -----------------------------
# 3️⃣ Tạo bảng nếu chưa có
# -----------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS places (
    CODE VARCHAR(20) PRIMARY KEY,
    LOCATION VARCHAR(255),
    TYPE VARCHAR(100),
    RATING DECIMAL(3,1),
    Address TEXT,
    Description TEXT,
    Long_Description TEXT,
    Tags_Creation_Description TEXT,
    Ticket_Info TEXT,
    image_path TEXT,
    open_time VARCHAR(10),
    close_time VARCHAR(10),
    coordinate VARCHAR(100),
    tags TEXT
);
"""

# -----------------------------
# 4️⃣ Hàm insert CSV vào DB
# -----------------------------
def insert_csv_to_db(csv_path, conn):
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sql = """
                REPLACE INTO places
                (CODE, LOCATION, TYPE, RATING, Address, Description, Long_Description,
                 Tags_Creation_Description, Ticket_Info, image_path, open_time, close_time,
                 coordinate, tags)
                VALUES (%(CODE)s, %(LOCATION)s, %(TYPE)s, %(RATING (MAX = 5))s, %(Address)s,
                        %(Description)s, %(Long Description)s, %(Tags_Creation_Description)s,
                        %(Ticket Info)s, %(image_path)s, %(open_time)s, %(close_time)s,
                        %(coordinate)s, %(tags)s)
            """
            cursor.execute(sql, row)
    conn.commit()
    cursor.close()
    print(f"✅ Đã insert dữ liệu từ {csv_path} vào DB.")

# -----------------------------
# 5️⃣ Chạy toàn bộ pipeline
# -----------------------------
if __name__ == "__main__":
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_SQL)
        cursor.close()

        insert_csv_to_db("../data/clean/restaurants.csv", conn)
        insert_csv_to_db("../data/clean/attractions.csv", conn)
        insert_csv_to_db("../data/clean/hotels.csv", conn)

        conn.close()
        print("🎉 Hoàn tất toàn bộ pipeline ETL → Database!")
