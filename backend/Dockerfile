# Backend image (SPEC 13 §4) — slim. Migration chạy lúc khởi động (alembic upgrade head).
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Áp migration rồi chạy server (SPEC 13 §4).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
