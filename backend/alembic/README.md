# Alembic migrations

Quản lý schema CSDL (SPEC 10 §5).

```bash
# Tạo migration mới sau khi đổi model
alembic revision --autogenerate -m "mô tả"

# Áp dụng tới bản mới nhất
alembic upgrade head

# Lùi 1 bản
alembic downgrade -1
```

URL lấy tự động từ `app.core.config` (đồng bộ hoá từ `DATABASE_URL`).
