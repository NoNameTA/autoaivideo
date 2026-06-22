# 04 — BACKEND SPEC

> FastAPI. Python 3.11+. Là bộ não điều phối: API, orchestrator, queue, plugin host. Tham chiếu `02`, `09`, `10`.

---

## 1. Cấu trúc app

```
backend/app/
├── main.py            # tạo FastAPI, mount routers, startup/shutdown
├── core/              # config (pydantic-settings), security, logging, errors
├── api/
│   ├── deps.py        # dependencies (auth, db session)
│   ├── rest/          # routers: projects, batches, jobs, agents, plugins
│   └── ws/            # websocket endpoints
├── models/            # SQLAlchemy ORM (xem 10)
├── schemas/           # Pydantic request/response
├── services/          # ProjectService, BatchService, JobService...
├── orchestrator/      # engine.py, queue.py, dispatcher.py, retry.py
├── plugins/           # loader.py, base.py, registry.py
└── db/                # session.py (async), migrations (alembic)
```

## 2. REST API (chính)

Base: `/api/v1`. Auth: Bearer token (xem `11`). Lỗi: `09 §6`.

| Method | Path | Mô tả |
|--------|------|------|
| GET/POST | `/projects` | List/Create project |
| GET/PATCH/DELETE | `/projects/{id}` | Chi tiết/Sửa/Xoá |
| POST | `/projects/{id}/batches` | Tạo batch (kèm danh sách input) |
| GET | `/batches/{id}` | Trạng thái batch + tổng hợp |
| GET | `/batches/{id}/jobs` | List job (phân trang, filter trạng thái) |
| GET | `/jobs/{id}` | Chi tiết job + steps |
| POST | `/jobs/{id}/retry` | Retry job/step failed |
| POST | `/jobs/{id}/cancel` | Huỷ job |
| GET | `/agents` | List agent + heartbeat |
| GET/POST | `/plugins` | List/Đăng ký plugin |
| GET | `/plugins/{name}/schema` | JSON Schema config plugin |
| GET | `/health`, `/ready` | Healthcheck |

## 3. WebSocket

- `/ws` (frontend): client `subscribe` theo `batch_id`/`job_id`; server đẩy `job.updated`, `step.updated`, `agent.updated`.
- `/ws/agent` (agent): kênh điều khiển, xem `05` và `09`.

## 4. Orchestrator Engine

Trách nhiệm: từ Job → quyết định Step kế tiếp → enqueue → nhận kết quả → cập nhật.

### Máy trạng thái Step
```
queued ──assign──► assigned ──ack──► running ──ok──► completed
   ▲                   │                 │
   │                   └──timeout────────┴──err──► failed ──retry?──► retrying ──► queued
```
- `assigned` quá `ack_timeout` (mặc định 30s) → requeue.
- `running` không heartbeat quá `heartbeat_timeout` (mặc định 120s) → fail/requeue.
- `failed` + `attempt < max_retries` + lỗi `transient` → `retrying` (backoff `base * 2^attempt`).

### Queue (durable)
- Bảng `job_queue` (xem `10`): hàng đợi bền, không mất khi restart.
- Khi enqueue: insert dòng `pending`. Dispatcher lấy theo ưu tiên + thời điểm.
- Đồng thời giới hạn bởi `max_concurrent_steps` (global) và `agent.capacity`.

### Dispatcher
- Chọn agent: `online` + có `capability` khớp `adapter` của step + còn slot.
- Gửi `step.assign` qua WS agent. Nếu không có agent phù hợp → step chờ.

## 5. Services (business logic)

- `BatchService.create()` — parse input rows → tạo Job + Step theo pipeline template → set `queued`.
- `JobService.advance()` — gọi engine sau mỗi step xong.
- `AgentService.register/heartbeat()` — quản lý vòng đời agent.
- `PluginService` — load registry, validate config theo schema.

## 6. Cấu hình (pydantic-settings, từ env)

```
APP_ENV=dev|prod
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
DATA_DIR=./data
AUTH_TOKEN=...            # xem 11
MAX_CONCURRENT_STEPS=4
ACK_TIMEOUT=30
HEARTBEAT_TIMEOUT=120
CORS_ORIGINS=http://localhost:5173
```

## 7. Logging & lỗi

- Log JSON, có `trace_id`, `job_id`, `step_id`.
- Exception → handler chuẩn trả lỗi theo `09 §6`.
- Phân loại lỗi adapter: `TransientError` vs `PermanentError` (base class trong plugins).

## 8. Khởi động/tắt

- Startup: kết nối DB, chạy migration check, khôi phục queue (requeue step treo), mở WS.
- Shutdown: drain, đánh dấu agent disconnect, đóng DB.
