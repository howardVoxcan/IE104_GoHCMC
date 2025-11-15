# Sử dụng image Python nhẹ
FROM python:3.11-slim

# Biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Thư mục làm việc
WORKDIR /app

# Cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .

# Collect static (nếu có)
RUN python manage.py collectstatic --noinput || true

# Chạy server Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
