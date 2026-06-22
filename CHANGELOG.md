# CHANGELOG — Source Code

> Lịch sử sinh mã nguồn (khác với spec `AI_VIDEO_AUTOMATION_SPEC/17_CHANGELOG.md`). Theo [Keep a Changelog](https://keepachangelog.com/) + SemVer.

## [Unreleased]

### Phase 5 — Plugin System (2026-06-22)
> SPEC 06, 08, 14. Plugin SDK ổn định + lifecycle + contract; adapter thật cho app verify được trên máy.

#### Added — Plugin SDK (agent)
- `agent/sdk.py` — `Adapter` ABC (capability, lifecycle `validate_config→prepare→run→collect→cleanup`), `StepContext`, `ProcessDriver`, `Asset`, `TransientError`/`PermanentError`, `SDK_VERSION`.
- `agent/plugin_loader.py` — nạp plugin từ `plugins/<name>/`: đọc `manifest.yaml`, **cổng free-only** (SPEC 14), import `adapter.py` theo entrypoint, khớp capability; plugin lỗi bị bỏ qua an toàn.
- `agent/adapter_registry.py` — gộp adapter built-in (`cli.run`) + plugin nạp động; cung cấp `capabilities()`.
- Refactor `adapters/cli_run.py`, `runner.py` (chạy đúng lifecycle SDK), `connection.py` (map `TransientError`→retryable).

#### Added — 3 plugin thật (plugins/)
- `plugins/ffmpeg/` (capability `video.ffmpeg`, cli-process) — manifest+adapter+schema+README.
- `plugins/yt_dlp/` (capability `media.download`, cli-process).
- `plugins/chrome/` (capability `web.cdp`, web-cdp) — điều khiển Chrome headless qua DevTools Protocol, screenshot.
- Mỗi plugin: `manifest.yaml` + `adapter.py` + `config.schema.json` + `README.md` (đúng SPEC 08 §2).

#### Added — Backend
- `app/plugins/loader.py` — quét `plugins/`, nhúng `config_schema`, **đồng bộ vào DB** lúc khởi động (giữ `enabled`/`config` người dùng); cổng free-only. Plugin Manager (frontend) + `/plugins/{name}/schema` dùng dữ liệu thật.

#### Added — Contract test (SPEC 08 §9, 15 §3)
- `agent/tests/test_plugin_contract.py` — kiểm tra manifest đủ trường, `free is True`, JSON Schema hợp lệ, adapter subclass + capability khớp + có `run`, loader nạp đủ 3 capability. **4 test pass.**

#### Deps
- Thêm `PyYAML==6.0.2` (backend + agent) cho manifest YAML.

#### Verified (thật)
- Backend: ruff ✅ · pytest ✅ **22 passed**. Agent: ruff ✅ · pytest ✅ **4 passed (contract)**.
- **Live adapter (thật) ✅**: FFmpeg tạo `out.mp4` (2326B) offline; Chrome CDP chụp `screenshot.png` (5261B) headless; yt-dlp v2026.06.09 sẵn sàng. RESULT PASS.

### Phase 4 — Workflow & Queue + Desktop Agent tối thiểu (2026-06-22)
> Quyết định người dùng: gộp 1 Desktop Agent thật để chạy job end-to-end thật (không mock). SPEC 02 §3, 04 §4, 05, 09 §4.

#### Added — Orchestrator (backend)
- `orchestrator/queue.py` (hàng đợi bền: enqueue/due_pending/leased_expired/mark_done/active_count), `retry.py` (backoff luỹ thừa), `agent_registry.py` (kết nối agent online + chọn theo capability+slot), `dispatcher.py` (dựng step.assign).
- `orchestrator/engine.py` — engine chạy nền (asyncio): dispatch theo `max_concurrent_steps`+capacity, máy trạng thái step `queued→assigned→running→completed|failed|retrying`, ack/heartbeat timeout → requeue, retry/backoff, **resume-on-startup** (requeue step treo), advance job → enqueue step kế/hoàn tất, cập nhật batch counts + broadcast realtime.
- Wire: `BatchService.create` đẩy step đầu vào queue + nhúng job vars vào `step.inputs`; `/ws/agent` đăng ký registry + chuyển kết quả về engine; lifespan start/stop engine + resume.
- Pipeline `local_demo.json` (adapter `cli.run`, free-only).

#### Added — Desktop Agent tối thiểu (thật)
- `agent/`: `drivers/process.py` (spawn process thật), `adapters/cli_run.py` (capability `cli.run`, chạy lệnh + thu file→asset+sha256), `fs.py` (thư mục asset SPEC 07), `runner.py`, `connection.py` (WS client: register/heartbeat/nhận assign/ack/completed/failed + reconnect), `main.py`.

#### Fixed
- ruff E501/UP041; `process.py` dùng builtin `TimeoutError`.

#### Verified
- Backend: ruff ✅ · pytest ✅ **22 passed** (thêm `test_orchestrator`: retry, enqueue, advance→completed, fail→failed, retry→requeue, asset persist).
- **End-to-end THẬT** ✅: chạy backend + agent thật → tạo batch `local_demo` 2 job → engine điều phối → agent spawn process Python thật → tạo file thật (`input.json` chứa job vars `{"topic":"A"}`, `result.txt`) → cả 2 job `completed`. RESULT PASS.
- Frontend build ✅ · agent ruff ✅.

### Phase 3 — Frontend Foundation (2026-06-22)
> Nối UI ↔ API thật (backend đã có ở phase trước). Đã duyệt: thêm RHF+Zod; hoãn virtualization; BrowserRouter+404.html (Phase Deploy).

#### Added
- **Infra**: `types/api.ts` (khớp schema backend), `store/{settings,ui}.ts` (token/apiBase/theme persist localStorage + ws status + toasts), `api/{client,endpoints,hooks}.ts` (REST client gắn token + React Query), `api/ws.ts` (WS client reconnect/backoff), `hooks/useWebSocket.ts` (kết nối + subscribe + invalidate cache realtime), `lib/format.ts` (status→màu SPEC 12 §4).
- **Components**: `StatusBadge`, `Toaster`, `Modal`, `JobGrid`, `StepTimeline`, `AgentCard`; forms RHF+Zod: `ProjectForm`, `PluginForm`, `BatchForm`.
- **Pages wired (API thật)**: Dashboard (info+agents+ws), Projects (list/create/delete), ProjectDetail, CreateBatch, BatchView (JobGrid + subscribe batch), JobDetail (StepTimeline + retry/cancel), DesktopAgent (agents), Plugins (register/enable/remove/schema), Settings (token/apiBase/theme + test kết nối).
- **Routing**: thêm `/projects/:id`, `/projects/:id/batches/new`, `/batches/:id`, `/jobs/:id` (SPEC 03 §3). Banner: thiếu token + đang kết nối lại WS (SPEC 12 §7). Theme dark/light (SPEC 12 §2).
- Deps: `react-hook-form`, `zod`, `@hookform/resolvers`.

#### Fixed
- `tailwind.config.js` + `postcss.config.js`: dùng glob/đường dẫn **tuyệt đối** (cwd-independent) để Tailwind sinh utility đúng dù chạy từ thư mục bất kỳ.

#### Verified (thật, trong trình duyệt)
- `npm run build` ✅ + `eslint` ✅ + `tsc --noEmit` ✅ (113KB gzip < 300KB target SPEC 03 §7).
- Chạy backend :8000 + Vite dev → trình duyệt preview: Dashboard hiển thị **Backend Online v2.0.0**, **Realtime đã kết nối** (WS), Projects load **dữ liệu thật** qua API có token (200). Theme dark + sidebar xanh đúng SPEC 12.

### Phase 2 (đã ĐẢO thứ tự) — Backend Foundation (2026-06-22)
> Quyết định người dùng: đảo Frontend↔Backend để Frontend nối API thật (tránh mock). Phạm vi = SPEC roadmap GĐ2: DB + ORM + REST API + WS hub. KHÔNG gồm orchestrator/execution (Phase Workflow & Queue).

#### Added
- **DB layer**: `db/base.py` (Declarative Base + TimestampMixin), `db/session.py` (async engine, SQLite WAL + foreign_keys), `db/ids.py` (ULID có tiền tố, tự hiện thực — không thêm dep).
- **Models (SPEC 10)**: projects, batches, jobs, steps, assets, agents, plugins, job_queue, events + enums.
- **Alembic (SPEC 10 §5)**: `alembic.ini`, `alembic/env.py` (URL đồng bộ từ config), migration `e90554295847_initial_schema` (9 bảng) — đã `upgrade head` thật.
- **Schemas (Pydantic)**: project, batch, job, step, asset, agent, plugin, common (Page/Error).
- **Services**: project, batch (sinh job+step từ template, transaction-safe, idempotency-key qua bảng events), job (get/retry/cancel), agent (register/heartbeat/offline), plugin (registry), pagination con trỏ.
- **REST API (SPEC 04 §2)**: projects CRUD, batches create/get + list jobs, jobs get/retry/cancel, agents list, plugins list/register/schema/update/remove, health/ready (ready kiểm tra DB).
- **WebSocket (SPEC 09 §3/§4)**: `/ws` (subscribe/broadcast) + `/ws/agent` (register/heartbeat → persist agent; step messages → Event + broadcast). ConnectionManager + envelope.
- **Core**: errors (envelope chuẩn SPEC 09 §6 + handlers), security (owner/agent token SPEC 11), constants (hết magic number).
- **Pipeline template**: `orchestrator/pipelines/faceless_v1.json` + `templates.py`.
- **Tests (SPEC 15)**: 16 test pass — health, auth (401/403 envelope), projects CRUD + validation, batches (sinh 3 job × 6 step, cancel, retry-409, idempotency, project-404), plugins lifecycle, websocket.

#### Fixed
- `logging.py`: ép stdout UTF-8 (Windows cp1252 gây UnicodeEncodeError với tiếng Việt).
- Endpoint 204 (`delete`) bỏ annotation `-> None` (FastAPI hiểu nhầm thành response_model).

#### Build/Test result
- Backend: ruff ✅ · pytest ✅ 16 passed · uvicorn thật ✅ (tạo project thật, 401/201 đúng).
- Frontend: `npm run build` ✅ (82KB gzip). Agent: chạy ✅.

### Phase 1 — Scaffold Project (2026-06-22)
#### Added
- Cấu trúc repo theo SPEC `02 §2`: `backend/`, `frontend/`, `agent/`, `plugins/`, `data/`, `.github/workflows/`.
- **Root**: `README.md`, `.gitignore`, `docker-compose.yml`, `CHANGELOG.md`, `.github/workflows/ci.yml`.
- **Backend**: FastAPI skeleton chạy được — `app/main.py` (`/health`, `/ready`, `/api/v1/info`), `core/config.py` (pydantic-settings theo SPEC `04 §6`), `core/logging.py`, router health, test `test_health.py`. `pyproject.toml` + `requirements.txt` + `.env.example` + `Dockerfile`.
- **Frontend**: Vite + React 18 + TS + Tailwind + React Router + Zustand + TanStack Query. Layout + 11 trang theo SPEC `12` (Dashboard, Projects, Workflow, Queue, File Manager, Desktop Agent, External Applications, Plugin Manager, Logs, Statistics, Settings). Design tokens theo SPEC `12 §2`. Build `npm run build` thành công.
- **Agent**: Python package chạy được — `agent/main.py`, `config.py`, `drivers/`, `adapters/`. `pyproject.toml` + `requirements.txt` + `.env.example`.
- **Plugins**: `plugins/README.md` (hướng dẫn cấu trúc theo SPEC `08`).

#### Notes
- Quyết định người dùng: giữ nguyên cấu trúc SPEC (`agent/`, `manifest.yaml`); không tạo `shared/scripts/docs`.
- Phase 1 là khung chạy được (scaffold thật, không placeholder giả) — chức năng đầy đủ thêm ở các phase sau.
