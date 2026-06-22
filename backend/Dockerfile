# Backend image (SPEC 13 §4) — slim, đa tầng tối giản.
FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Phase Backend Foundation sẽ thêm: alembic upgrade head trước khi chạy.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
