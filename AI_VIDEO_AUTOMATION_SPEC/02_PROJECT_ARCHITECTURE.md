# 02 — PROJECT ARCHITECTURE

> Kiến trúc kỹ thuật của AI Video Platform V2. Tham chiếu khái niệm từ `01_MASTER_SPEC.md`.

---

## 1. Thành phần (Components)

| Thành phần | Công nghệ | Vai trò |
|-----------|-----------|--------|
| **Frontend** | Vite + React + TypeScript + Tailwind | Dashboard, cấu hình, theo dõi |
| **Backend** | FastAPI (Python 3.11+), Uvicorn | API, orchestrator, queue, plugin host |
| **Database** | SQLite (mặc định) / PostgreSQL | Trạng thái bền vững |
| **Queue** | In-process asyncio queue + bảng `job_queue` (durable) | Điều phối Step |
| **Desktop Agent** | Python + Playwright (CDP) + pywinauto/UI automation | Điều khiển app ngoài |
| **Plugins** | Python entry-points | Adapter cho External Apps |
| **Realtime** | WebSocket (FastAPI) | Đẩy trạng thái |

## 2. Cấu trúc thư mục mã nguồn

```
C:\AIVideoPlatform\
├── AI_VIDEO_AUTOMATION_SPEC\   # Bộ spec này
├── backend\
│   ├── app\
│   │   ├── main.py             # FastAPI entry
│   │   ├── api\                # routers (REST + WS)
│   │   ├── core\               # config, security, logging
│   │   ├── models\             # SQLAlchemy ORM
│   │   ├── schemas\            # Pydantic DTO
│   │   ├── services\           # business logic
│   │   ├── orchestrator\       # pipeline engine + queue
│   │   ├── plugins\            # plugin loader + base
│   │   └── db\                 # session, migrations (Alembic)
│   ├── tests\
│   └── pyproject.toml
├── frontend\
│   ├── src\
│   │   ├── pages\
│   │   ├── components\
│   │   ├── store\              # Zustand
│   │   ├── api\                # client REST/WS
│   │   └── main.tsx
│   ├── index.html
│   └── package.json
├── agent\
│   ├── agent\
│   │   ├── main.py
│   │   ├── runner.py           # nhận Step, thực thi
│   │   ├── drivers\            # CDP, UI automation
│   │   └── adapters\           # impl plugin phía agent
│   └── pyproject.toml
├── plugins\                    # plugin cài thêm
├── data\                       # file system runtime (xem 07)
├── docker-compose.yml
└── README.md
```

## 3. Luồng điều phối (Orchestration)

```
Job(queued)
   └─► OrchestratorEngine.next_step()
         └─► JobQueue.enqueue(step)            # durable, bảng job_queue
               └─► Dispatcher.assign(agent)     # chọn agent rảnh + có capability
                     └─► WS: step.assign → Agent
                            └─► Agent.runner.run(step) via Driver/Adapter
                                  └─► WS: step.progress / step.completed / step.failed
                                        └─► Engine cập nhật DB → next_step() | retry | fail
```

### Trạng thái Job/Step
`queued → running → completed | failed | cancelled`
Step thêm: `assigned`, `retrying`. Quy tắc chuyển trạng thái: `04_BACKEND_SPEC.md §4`.

### Retry
- Mỗi Step có `max_retries` (mặc định 3), backoff luỹ thừa.
- Lỗi phân loại: `transient` (retry) vs `permanent` (fail ngay).

## 4. Pipeline & Template

Một **Pipeline** là DAG tuần tự các Step. Ví dụ template "Faceless Video":

```yaml
pipeline: faceless_v1
steps:
  - id: script      adapter: llm.free_chat        out: script.txt
  - id: voice       adapter: tts.free_tts         in: script.txt   out: voice.mp3
  - id: images      adapter: image.free_gen       in: script.txt   out: img/*.png
  - id: subtitle    adapter: subtitle.whisper     in: voice.mp3    out: subs.srt
  - id: assemble    adapter: video.ffmpeg         in: [img/*, voice.mp3, subs.srt]  out: final.mp4
  - id: export      adapter: export.local         in: final.mp4    out: export/
```

Pipeline lưu trong **bảng `pipelines` (DB)** — CRUD qua `/api/v1/pipelines` (tạo/sửa/xoá/chạy ở trang Workflow). Built-in template (JSON trên đĩa) được **seed vào DB lúc khởi động** (insert-if-missing); `get_steps` ưu tiên DB, fallback JSON. Adapter resolve qua Plugin SDK (`08`).

### 4.1 Video Sources — lớp nguồn dữ liệu đầu vào (SPEC 03, 10)

**Video Source** = nguồn cung cấp danh sách link video để chạy. Tách khỏi Workflow/Queue để **thêm
nguồn mới không phải sửa pipeline**:
- `source_type` mở rộng: `direct_url` (V1) · `google_sheets` (V2) · `csv` · `folder` · `google_drive`
  · `dropbox` · `onedrive`… Mỗi loại chỉ là cách **lấy ra danh sách URL**; phần sau giống nhau.
- **Run Workflow**: Website chuyển mỗi item (URL) thành **1 input row** → tạo **Batch** (Project→Batch→
  Job hiện có) với pipeline download → **Agent** tải bằng plugin `media.download` (yt-dlp). **Website chỉ
  tạo Job, Backend chỉ điều phối, Agent mới tải** (giữ kiến trúc `Website→Backend→Agent→Plugin→External`).
- Đọc nguồn cloud (Google Sheets…) đi qua **Backend→Adapter** cho Preview (không để Website gọi trực
  tiếp API ngoài); việc **tải video** luôn ở Agent. Logic đặc thù nằm ở Adapter/Plugin, **không** nhúng
  vào Website/Backend.

## 5. Giao tiếp giữa các thành phần

| Cặp | Kênh | Định dạng |
|-----|------|----------|
| Frontend ↔ Backend | REST (CRUD) + WS (realtime) | JSON (xem `09`) |
| Backend ↔ Agent | WebSocket bền (reconnect) | JSON message envelope (xem `09`) |
| Agent ↔ External App | CDP (Chromium) / UI automation | Lệnh driver |
| Backend ↔ DB | SQLAlchemy async | SQL |

## 6. Khả năng mở rộng & ràng buộc

- **Stateless backend** (trừ DB) → có thể chạy nhiều worker.
- **Agent nhiều máy**: mỗi agent đăng ký `capabilities` (adapter nó hỗ trợ). Dispatcher route theo capability.
- **Idempotency**: mỗi Step có `idempotency_key = job_id+step_id+attempt`.
- **Resume sau crash**: queue durable trong DB; khi backend khởi động lại, requeue các step `assigned/running` quá hạn heartbeat.

## 7. Quan sát (Observability)

- Log JSON có `trace_id` xuyên suốt Job→Step→Agent.
- Metrics: số job/giờ, tỉ lệ fail, thời gian từng adapter.
- Health endpoints: `/health`, `/ready`.
Chi tiết logging: `04_BACKEND_SPEC.md §7`, `11_SECURITY_SPEC.md §6`.
