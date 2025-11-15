FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libpq-dev \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip setuptools wheel

# Numpy trước để tránh lỗi thinc / spaCy
RUN pip install --no-cache-dir numpy==1.26.1

RUN pip install --no-cache-dir -r requirements.txt

# 🔥 ***THÊM DÒNG NÀY để tải model spaCy***
RUN python -m spacy download en_core_web_sm

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "GoHCMC.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
