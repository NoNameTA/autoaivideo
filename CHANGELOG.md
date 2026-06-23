# CHANGELOG — Source Code

> Lịch sử sinh mã nguồn (khác với spec `AI_VIDEO_AUTOMATION_SPEC/17_CHANGELOG.md`). Theo [Keep a Changelog](https://keepachangelog.com/) + SemVer.

## [Unreleased]

### UAT — Trang chức năng (5/5): External Applications (2026-06-23)
> 🏁 **Hoàn tất UAT 5/5 trang** (Workflow · Queue · Logs · Statistics · External Apps đều làm thật).
> External App (SPEC 06) = app ngoài bọc bởi Adapter (plugin), phân loại theo `type`
> (web-cdp/desktop-uia/cli-process/local-http). Trang này là **view vận hành**: loại tích hợp +
> **trạng thái kết nối** (agent online có capability) + **test kết nối** — khác Plugin Manager (lifecycle).

#### Added — Backend
- `services/external_app_service.py` — `ExternalAppService.list` (suy từ plugins + `connection`
  từ agent registry live: connected/no_agent/disabled) + `test` (**test kết nối THẬT**: free policy
  → enabled → có agent online hỗ trợ capability + còn slot; phản ánh khả năng dispatch thực tế,
  không mock). `AgentRegistry.online_for`/`has_free_slot`.
- `GET /api/v1/external-apps` + `POST /api/v1/external-apps/{name}/test`
  (`api/rest/external_apps.py`, `schemas/external_app.py`).

#### Added — Frontend
- Trang **External Applications** thật (`pages/ExternalApps.tsx`): lọc theo **loại tích hợp**,
  card mỗi app (loại/capability/version/enabled/free/license/nguồn↗), **badge trạng thái kết nối**,
  nút **Test kết nối** (kết quả inline + toast). Realtime: `agent.updated` invalidate `["external-apps"]`.
  Types `ExternalApp`/`ExternalAppTestResult`, endpoint + hook.

#### Verified
- Backend ruff ✅ · pytest ✅ **44 passed** (+4 `test_external_apps`: list, test disabled/no_agent/
  connected/404) · 1 skipped. Frontend lint ✅ · build ✅ (120.80 KB gzip).
- Browser (thật, 5 plugin thật trong DB): 5 app phân loại đúng (cli-process/desktop-uia/web-cdp),
  lọc theo loại, trạng thái kết nối, **Test kết nối trả kết quả thật** ("chưa có agent online…"),
  không lỗi (đã chụp).

### UAT — Trang chức năng (4/5): Statistics (2026-06-23)
> Thống kê từ **DATA THẬT** jobs/steps (SPEC 02 §7). Không dữ liệu giả. Biểu đồ **SVG tự vẽ**
> (không thêm dependency — giữ bundle nhẹ). Dashboard giữ KPI realtime + activity; Statistics là
> trang phân tích tổng hợp (không trùng).

#### Added — Backend
- `services/stats_service.py` — `StatsService.compute`: job/step theo status, **fail_rate**
  (failed/(completed+failed)), **throughput** (job completed/ngày, 14 ngày, điền 0), **adapter
  stats** (count/failed/avg_seconds từ `finished_at−started_at`). Tổng hợp Python (portable
  SQLite↔PG, tránh hàm dialect).
- `GET /api/v1/stats` (`api/rest/stats.py`, `schemas/stats.py`).

#### Added — Frontend
- Trang **Statistics** thật (`pages/Statistics.tsx`): KPI (tổng job/hoàn tất/tỉ lệ lỗi/tổng step),
  thanh phân bố job+step theo status (màu SPEC 12 §4), **biểu đồ throughput SVG cột**, bảng hiệu
  năng adapter (số lần/lỗi%/thời gian TB + thanh). Realtime qua `useWebSocket` invalidate `["stats"]`.
  Types `Stats`/`AdapterStat`/`ThroughputPoint`, endpoint `getStats`, hook `useStats`.

#### Verified
- Backend ruff ✅ · pytest ✅ **40 passed** (+2 `test_stats`: rỗng + có data: counts/fail_rate/
  avg_seconds/throughput) · 1 skipped. Frontend lint ✅ · build ✅ (120.10 KB gzip).
- Browser (thật, data thật trong DB: 6 job/11 step/2 adapter): KPI + thanh status + biểu đồ
  throughput SVG + bảng adapter hiển thị đúng, màu theo SPEC, không lỗi (đã chụp).

### UAT — Trang chức năng (3/5): Logs (2026-06-23)
> **Điểm thiết kế (đã chốt với user):** bảng `events` (SPEC 10 §2 = audit/log) trước đây
> chỉ dùng cho idempotency key; activity chỉ broadcast WS, **không persist**, và **chưa có
> trường `level`**. Quyết định: **persist mọi activity vào `events`** (biến nó thành audit-log
> thật) + **thêm cột `level` suy ra từ loại event lúc ghi** (`level_for`). Không thêm bảng mới.
> Cập nhật SPEC 04 §7 + 10 §2.

#### Added — Backend
- Cột `events.level` (`info|warn|error|debug`, có index) + migration `b2c4e6f80a11`. Suy ở
  thời điểm ghi từ loại event (`*.failed`→error, retry/timeout/disabled/removed/cancelled→warn,
  progress→debug, còn lại→info).
- `services/event_service.py` — `EventService`: `level_for` (thuần), `from_activity`
  (suy entity_type/entity_id), `record` (transaction riêng: persist + broadcast `activity`,
  **làm giàu** `batch_id`/`project_id` để lọc), `list` (lọc level/category/project/batch/plugin/
  trace_id/search qua `json_extract`). Loại `idempotency_batch` không hiện ở Logs.
- `GET /api/v1/logs` (`api/rest/logs.py`, `schemas/log.py`). Engine `_activity` + plugin
  `_lifecycle` nay đi qua `EventService` (vừa ghi DB vừa phát realtime); `job.updated` kèm `batch_id`.

#### Added — Frontend
- Trang **Logs** thật (`pages/Logs.tsx`): bảng audit-log mới-nhất-trước, **lọc theo level**
  (tabs có đếm) + **nhóm** (job/step/plugin/agent/fs/system) + **tìm kiếm** (debounce, gồm
  trace_id/batch/project), badge màu theo level, link Job/Batch, chỉ báo `● live`, scroll dính header.
- Realtime: `useWebSocket` invalidate key `["logs"]` khi có `activity`/`fs.event`/`agent.updated`.
  Types `LogEntry`/`LogQuery`, endpoint `listLogs`, hook `useLogs`.

#### Verified
- Backend ruff ✅ · pytest ✅ **38 passed** (+4 `test_logs`: level_for, persist+lọc API, lọc
  batch/project, loại event nội bộ) · 1 skipped (e2e). Frontend lint ✅ · build ✅ (118.69 KB gzip).
- Browser (thật): trang Logs hiển thị event thật, lọc level + đếm số đúng, **realtime tự cập nhật
  qua WS không refresh** (sinh event qua API → bảng thêm dòng), không lỗi console.

### UAT — Trang chức năng (2/5): Queue (2026-06-23)
#### Added — Backend
- `JobService.list_all` + `GET /api/v1/jobs` (list job toàn cục, lọc `status` + `search` job/batch id, mới nhất trước). Test `test_jobs.py`.
#### Added — Frontend
- Trang **Queue** thật: bảng job realtime (WS invalidate `jobs-all`), **filter tabs có đếm số** + **tìm kiếm** (debounce), **retry/cancel** theo trạng thái, link Job/Batch. Loading/empty/error, responsive (overflow-x).
#### Verified
- Backend ruff ✅ · pytest ✅ **34 passed** (+2). Frontend lint ✅ · build ✅. Browser: Queue hiển thị 6 job + filter count + search (đã chụp).

### UAT — Trang chức năng (1/5): Workflow (2026-06-23)
> User chốt: editor đầy đủ (vượt SPEC V2.0); cập nhật SPEC 02 §4 + 03 §5. Pipeline lưu DB.

#### Added — Backend
- Model `pipelines` + migration `793d0effa4d0`; `schemas/pipeline.py`; `services/pipeline_service.py` (list/get/create/update/delete + `get_steps` ưu tiên DB→fallback JSON + `sync_builtins` seed).
- REST `/api/v1/pipelines` (CRUD + `POST /{name}/run` = tạo batch). Seed built-in lúc khởi động.
- `batch_service` resolve step từ `PipelineService.get_steps` (thay vì chỉ JSON).

#### Added — Frontend
- Trang **Workflow** thật: list pipeline + **DAG các step**, editor tạo/sửa (thêm/xoá/sắp xếp step, adapter datalist, config JSON), xoá, **Run** (chọn project + inputs → batch → BatchView). Loading/empty/error, responsive.

#### Verified
- Backend ruff ✅ · pytest ✅ **32 passed** (+4 pipeline). Frontend lint ✅ · build ✅.
- Browser: trang Workflow hiển thị 4 pipeline built-in + DAG thật (đã chụp).

## [1.0.0] - 2026-06-23

> 🏁 **Bản phát hành ổn định đầu tiên** — hoàn thành Phase 1–10. Nền tảng tự động hoá video AI chạy thật end-to-end + **deploy thật** (GitHub Pages live, CI xanh, Docker smoke PASS).

### Release notes — v1.0.0
- **Frontend** (Vite/React/TS/Tailwind) → **GitHub Pages live**: https://nonameta.github.io/autoaivideo/ (BrowserRouter + `404.html` SPA fallback, refresh mọi route OK).
- **Backend** (FastAPI + SQLAlchemy + SQLite + WebSocket): REST CRUD (project/batch/job/agent/plugin), orchestrator (durable queue, state machine, retry/backoff, ack/heartbeat timeout, resume), WS hub, plugin registry, **File Manager + Permission Manager** (Allowed Folders). Docker-ready (`docker compose` + alembic entrypoint).
- **Desktop Agent** (Python + bản `.exe` PyInstaller): WS client (reconnect), drivers **Process / CDP (raw DevTools) / UIA (pywinauto)**, File Manager + **Watch realtime** (watchdog, chuẩn hoá + debounce).
- **Plugin SDK** + plugin thật: `ffmpeg`, `yt-dlp`, `chrome`, `edge`, `notepad` (contract test, free-only gate).
- **Dashboard realtime**: job/progress, `fs.event`, `plugin.runtime.*`, `plugin.lifecycle.*` (Activity Stream có bộ lọc).
- **Chất lượng & vận hành**: CI 3 job (lint + pytest + build), E2E thật (gated `RUN_E2E=1`), Docker smoke PASS, INSTALL.md verified trên môi trường sạch.
- Tag liên quan: `v0.8.0` (Deployment), `v0.9.0` (Desktop Agent Full).

### Roadmap sau v1.0.0
- **UAT** (User Acceptance Testing) — dùng thực tế, sửa lỗi phát sinh.
- Sau UAT ổn định → Adapter: **1) Google Sheets · 2) OBS · 3) Bulk Video Studio**.
- **Prompt Engine** — sau khi các adapter cốt lõi hoàn thiện.

### Phase 10 — Real Deployment (2026-06-22)
#### Done
- Xác minh **INSTALL.md từ môi trường sạch**: Backend (venv + alembic + /health=200), Frontend (`npm ci` + build + 404.html), Agent (venv + chạy), Agent .exe (Phase 9).
- **Push source + tags** lên GitHub `NoNameTA/autoaivideo`: `main`, `v0.8.0`, `v0.9.0`.
- **GitHub Actions CI: 3/3 job XANH** (Backend / Agent / Frontend).
- **🌐 GitHub Pages LIVE & verified**: `https://nonameta.github.io/autoaivideo/` → HTTP 200, title đúng, base `/autoaivideo/`; **refresh route sâu** (`/projects/...`) phục vụ `404.html` (SPA fallback) — hoạt động.

#### Fixed (để CI/Deploy chạy được)
- `db/session.py`: tự tạo thư mục SQLite (CI thiếu `backend/data/`).
- `agent/tests/__init__.py`: pytest tìm thấy package `agent` trên CI.
- `tests/conftest.py`: lifespan (sync_plugins/SELECT 1) dùng DB test có schema.
- 2 workflow: **ghim toàn bộ action sang full commit SHA** (đáp ứng repo policy).
- Repo settings (owner): bật Actions → "Allow all actions"; bỏ "Require actions pinned to full SHA" (vì `upload-pages-artifact` gọi `upload-artifact` nội bộ bằng tag).

#### Docker smoke test ✅ (2026-06-23)
- `docker compose up -d --build` → container Up; `alembic upgrade head` chạy 2 migration trong container; uvicorn lên.
- Smoke: `/health`=200, `/ready`=200 (DB check), `/api/v1/info` v2.0.0 (env=prod), POST project (auth)=201. **PASS**.
- Fix: `core/config.py` dùng `NoDecode` cho `cors_origins` (pydantic-settings JSON-decode env list trước validator → lỗi khi `CORS_ORIGINS` là chuỗi trong compose).

**Phase 10 hoàn tất.** Website live + CI xanh + Docker smoke PASS + INSTALL.md verified.

### Phase 9 — Desktop Agent Full (2026-06-22)
> SPEC 05 §4. Quyết định người dùng: CDP = raw DevTools Protocol (không Playwright); UIA verify bằng Notepad; plugin qua .exe = ffmpeg + chrome.

#### Added — Drivers (agent)
- `agent/drivers/cdp.py` — **CDP driver nâng cao** (raw CDP qua websockets+httpx): `launch/goto/eval/wait_for/click/type/title/screenshot/close`. Chrome & Edge.
- `agent/drivers/uia.py` — **UIA driver** (pywinauto): `start (kết nối cửa sổ theo title qua Desktop) / focus_window / type_keys / get_text / close` (đóng bằng PID, tránh hộp thoại Save). Dep `pywinauto` (Windows-only).

#### Added — Plugins (External App adapters)
- Refactor `plugins/chrome` dùng `CdpDriver` (goto + đọc title + screenshot).
- `plugins/edge` (`web.cdp.edge`) — Edge headless qua CDP.
- `plugins/notepad` (`desktop.notepad`) — minh hoạ UIA: mở Notepad, gõ text, đọc lại → asset.
- Pipeline `agent_full_demo.json` (video.ffmpeg + web.cdp) cho E2E qua .exe.

#### Changed
- `build_exe.py`: hidden-import `agent.drivers.cdp/uia` + collect-all `httpx` (driver chỉ plugin nạp động dùng → PyInstaller không tự thấy). Exe nạp đủ 6 capability.
- SPEC `05 §4` cập nhật: CDP raw (không Playwright), thêm Edge.

#### Verified
- Backend pytest ✅ 28 passed (1 e2e skip) · Agent ruff ✅ · pytest ✅ 15 passed (+3 driver).
- **CDP nâng cao (thật) ✅**: Chrome & Edge headless → `goto`+`eval(title)=AIVID`+`screenshot.png`.
- **🎯 E2E qua Agent .exe (thật) ✅**: `aivideo-agent.exe` nạp đủ plugin, chạy `agent_full_demo` → **out.mp4 (ffmpeg) + screenshot.png (chrome)** + job completed. RESULT PASS.

#### Pending Verification
- **UIA Notepad live**: code thật (pywinauto), nhưng môi trường chạy tool **không có desktop tương tác** (`WaitForInputIdle failed`) → chưa verify live ở đây. Chạy trên desktop thật sẽ hoạt động.

## [0.8.0] - 2026-06-22

> Mốc **Semantic Versioning** đầu tiên (SPEC 13 §7). `0.8.0` gói toàn bộ Phase 1–8 (mỗi phase ~ 1 minor:
> 0.1 Scaffold · 0.2 Backend · 0.3 Frontend · 0.4 Workflow+Agent · 0.5 Plugin · 0.6 File Manager · 0.7 Integration&Testing · 0.8 Deployment). Chi tiết theo từng Phase bên dưới.

### Phase 8 — GitHub Pages Deployment (2026-06-22)
> SPEC 13. Quyết định người dùng: cấu hình + verify local (không push repo); chỉ tạo compose (Docker smoke Pending).

#### Added
- **404.html SPA fallback**: script `postbuild` copy `dist/index.html` → `dist/404.html`; base động qua `VITE_BASE`.
- **Workflow** `.github/workflows/frontend-pages.yml`: build (base = `/<repo>/`) + `upload-pages-artifact` + `deploy-pages`.
- **PyInstaller**: `agent/run.py` (entry), `agent/build_exe.py` → `dist/aivideo-agent.exe`. Agent config `plugins_dir` (env `PLUGINS_DIR`) để exe nạp plugin từ thư mục.
- **INSTALL.md**: hướng dẫn cài đặt & chạy Frontend / Backend / Agent / Plugin / Pages / smoke.
- `Dockerfile`: entrypoint chạy `alembic upgrade head` trước uvicorn (SPEC 13 §4). `.gitignore`: loại `agent/build|dist`, `*.spec`.

#### Verified
- Frontend: `npm run build` (base `/aivideo/`) ✅ — **404.html = index.html**, assets đúng base.
- **SPA-refresh (browser) ✅**: mở trực tiếp route sâu `/aivideo/projects/...` render đúng trang (vite preview mô phỏng GH Pages) — đã chụp.
- **Agent .exe (thật) ✅**: `aivideo-agent.exe` nạp plugin từ `PLUGINS_DIR`, đăng ký backend đầy đủ `['cli.run','media.download','video.ffmpeg','web.cdp']`, online.
- Backend pytest ✅ · Agent pytest ✅.

#### Pending Verification
- **Deploy Pages thật**: chưa push (AIVideoPlatform chưa có remote) — cấu hình sẵn sàng, user tự tạo repo + bật Pages.
- **Docker compose smoke**: Docker chưa cài trên máy → chưa chạy `docker compose up`. Compose + Dockerfile đã hoàn thiện.

### Phase 7 — Integration & Testing (2026-06-22)
> SPEC 15. Quyết định người dùng: E2E thật bằng `cli.run`/`video.ffmpeg` (không mock); E2E local-only, CI chạy unit/build; Dashboard Activity Stream phân loại `plugin.runtime.*` + `plugin.lifecycle.*`.

#### Added — Activity Stream (backend)
- `plugins/registry_cache.py` — cache capability plugin để engine phân biệt step plugin vs built-in.
- Engine phát **global `activity`**: `job.updated`, `plugin.runtime.{started,progress,finished,failed}` (cho step do plugin chạy).
- `PluginService` phát `plugin.lifecycle.{installed,enabled,disabled,updated,removed}`; sync cập nhật registry_cache.
- Pipeline `ffmpeg_demo.json` (1 step `video.ffmpeg`) cho E2E.

#### Added — Dashboard realtime (frontend)
- `ui` store: buffer `activities` + `pushActivity`. `useWebSocket`: phân loại `activity`/`fs.event`/`agent.updated` → feed.
- **Dashboard "Hoạt động realtime"**: panel + bộ lọc (Tất cả/Job/Plugin runtime/Plugin lifecycle/FS/Agent), màu phân loại.

#### Added — Tests
- `tests/test_recovery.py` (integration): resume requeue step đang chạy + agent→offline; ack-timeout requeue.
- `tests/e2e/test_pipeline_e2e.py` (**gated `RUN_E2E=1`**): backend+agent subprocess thật chạy `ffmpeg_demo` → job completed + asset `out.mp4` thật + Dashboard nhận `plugin.runtime.*` + `job.updated`.
- conftest: marker `e2e` + skip khi không có `RUN_E2E=1`.

#### Changed — CI / SPEC
- `.github/workflows/ci.yml`: 3 job (Backend/Frontend/Agent) — install + lint + test/build + summary; agent thêm pytest.
- SPEC `09 §4.2` (Activity Stream global), SPEC `15` (E2E thật + CI gate).

#### Verified
- Backend: ruff ✅ · pytest ✅ **28 passed, 1 skipped (e2e)**. Agent: ruff ✅ · pytest ✅ **12 passed**. Frontend: lint ✅ · build ✅ (115KB gzip).
- **E2E THẬT (`RUN_E2E=1`) ✅**: full pipeline Web→…→Dashboard, job completed + `out.mp4` thật + realtime activity. RESULT PASS.
- **Dashboard realtime (browser) ✅**: panel Hoạt động realtime hiển thị `job` + `plugin.runtime` thật (đã chụp màn hình).

### Phase 6.1 — Watch Folder realtime nâng cấp (2026-06-22)
> Hoàn thiện watchdog theo yêu cầu. Cập nhật SPEC 07 §8 + SPEC 09 §4.1.

#### Changed — Agent
- `watcher.py` viết lại: **chuẩn hoá** sự kiện về 4 loại `created/modified/deleted/moved`; **Permission Manager lọc từng sự kiện** trước khi gửi; **reconcile** (watch = đã-yêu-cầu ∩ allowed ∩ thư-mục) → **tự start/stop khi Allowed Folders đổi**.
- `connection.py`: **coalesce/debounce** sự kiện trùng `(type,path,dest_path)` trong cửa sổ `watch_debounce_ms` (mặc định 200ms) trước khi gửi `fs.event`; `config.update` gọi `watcher.reconcile()`.
- `fs_manager.PermissionManager`: thêm `is_allowed()` (không raise) cho watcher lọc. Config thêm `watch_debounce_ms`.

#### Added — Tests
- `agent/tests/test_watcher.py`: chuẩn hoá+lọc loại, coalesce giữ mới nhất, **sự kiện watchdog thật** (tạo file → nhận event), reconcile gỡ watch khi folder rời Allowed Folders.

#### Changed — SPEC
- `07_FILE_SYSTEM_SPEC.md` §8 (Watch Folder realtime). `09_COMMUNICATION_PROTOCOL.md` §4.1 (fs.request/fs.response/fs.event + config.update allowed_folders).

#### Verified
- Agent: ruff ✅ · pytest ✅ **12 passed**. Backend: pytest ✅ **26 passed**. Frontend: build ✅.
- **End-to-end realtime THẬT** ✅: agent watch thư mục → tạo/sửa/xoá file → `fs.event` (created/modified/deleted, chuẩn hoá + coalesce) tới dashboard WS. RESULT PASS.

### Phase 6 — File Manager (2026-06-22)
> SPEC 07 + 11 §5. Quyết định người dùng: RPC fs.request/fs.response qua /ws/agent; Allowed Folders trong DB đẩy xuống agent; watchdog cho watch realtime.

#### Added — Backend
- Model `allowed_folders` + migration `141a508530c2`; `schemas/fs.py`; `services/allowed_folder_service.py` (CRUD + `is_within_allowed` chống traversal).
- `api/ws/fs_rpc.py` — RPC correlation-id qua `/ws/agent` (backend chờ Future).
- `services/fs_service.py` — validate Allowed Folders (Permission Manager) rồi forward tới agent; `push_allowed` đẩy danh sách xuống agent.
- `api/rest/fs.py` — `/api/v1/fs/{allowed (CRUD), scan, read, metadata, copy, move, rename, delete, watch}`.
- `agent_registry`: `first_agent_id` + `send_all`; ws/agent xử lý `fs.response`/`fs.event`, đẩy `config.update{allowed_folders}` khi agent register; lỗi `AGENT_UNAVAILABLE`/`FS_ERROR`.

#### Added — Agent (tích hợp Desktop Agent + Plugin System)
- `fs_manager.py` — `PermissionManager` (realpath + prefix, chống traversal) + thao tác thật: scan/read/copy/move/rename/delete/metadata.
- `watcher.py` — Folder Watcher dùng `watchdog`, emit `fs.event` thread-safe về backend.
- `connection.py` — xử lý `config.update` (cập nhật Allowed Folders), `fs.request` → fs_manager → `fs.response`. Dep `watchdog==6.0.0`.

#### Added — Frontend
- `types/fs.ts`, endpoints FS; trang **File Manager** thật: quản lý Allowed Folders, duyệt thư mục, Read/Info/Rename/Copy/Move/Delete, bật Watch + nhận `fs.event` realtime.

#### Added — Tests
- Backend `test_fs.py` (Allowed CRUD, traversal util, scan no-agent→503, ngoài allowed→403). Agent `test_fs_manager.py` (thao tác file thật + từ chối quyền).

#### Verified
- Backend: ruff ✅ · pytest ✅ **26 passed**. Agent: ruff ✅ · pytest ✅ **8 passed**. Frontend: lint ✅ · `npm run build` ✅ (114KB gzip).
- **End-to-end THẬT** ✅: backend + agent → thêm Allowed Folder → scan/metadata/read/copy/rename/move/delete file thật + watch bật; path ngoài allowed bị chặn **403**. RESULT PASS.

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
