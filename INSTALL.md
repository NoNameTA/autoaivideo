# Hướng dẫn cài đặt & chạy — AI Video Platform V2

> Tham chiếu SPEC `13_GITHUB_DEPLOYMENT.md`. Yêu cầu: **Python 3.11+**, **Node.js 18+**, (tuỳ chọn) Docker. Chỉ phần mềm miễn phí (SPEC 14).

## Kiến trúc tổng quan

```
┌──────────────┐  REST + WebSocket  ┌───────────────┐  WebSocket (RPC)  ┌────────────────┐  CDP / UIA / CLI  ┌───────────────┐
│   Frontend   │ ─────────────────▶ │    Backend    │ ────────────────▶ │ Desktop Agent  │ ────────────────▶ │ External App  │
│ (Vite/React) │ ◀───────────────── │   (FastAPI)   │ ◀──────────────── │ (Python / .exe)│ ◀──────────────── │   + Plugin    │
│  Dashboard   │  job/fs/activity   │ Queue+Engine  │  step / fs.event  │  Plugin host   │   asset / event   └───────────────┘
└──────────────┘   (realtime WS)    │  SQLite + WS  │                   │ File + Watcher │
                                    └───────────────┘                   └────────────────┘
```

**Frontend → Backend → Desktop Agent → Plugin/External App.** Website KHÔNG truy cập file hay điều
khiển Windows trực tiếp — mọi thao tác đi qua Backend rồi tới Agent (SPEC 11). Plugin nạp động ở Agent
(SPEC 08); realtime (job/progress/fs.event/plugin event) đẩy về Dashboard qua WebSocket (SPEC 09).

## 0. Lấy mã nguồn

```bash
git clone <repo-url> AIVideoPlatform
cd AIVideoPlatform
```

---

## 1. Backend (FastAPI)

```bash
cd backend
python -m pip install -r requirements.txt
# Tạo schema (SQLite mặc định data/app.db)
alembic upgrade head
# Chạy
uvicorn app.main:app --reload --port 8000
```

- Kiểm tra: http://localhost:8000/health → `{"status":"ok"}`.
- Cấu hình (tuỳ chọn) qua `.env` (xem `backend/.env.example`): `AUTH_TOKEN`, `AGENT_TOKEN`, `DATABASE_URL`, `DATA_DIR`, `CORS_ORIGINS`...

### Docker (tuỳ chọn)
```bash
docker compose up -d        # backend tại :8000, tự alembic upgrade head
```

---

## 2. Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173 (proxy /api,/ws -> :8000)
```

Build production:
```bash
npm run build               # -> dist/ (kèm 404.html SPA fallback)
```

Lần đầu mở web: vào **Settings** nhập **Owner Token** (mặc định `change-me-owner-token`) + API Base URL (trống nếu dùng proxy dev).

---

## 3. Desktop Agent (Python / .exe)

### Chạy từ mã nguồn
```bash
cd agent
python -m pip install -r requirements.txt
set BACKEND_WS_URL=ws://localhost:8000/ws/agent
set AGENT_TOKEN=change-me-agent-token
set AGENT_ID=win-pc-01
python -m agent.main
```

### Bản đóng gói .exe (Windows)
```bash
cd agent
python build_exe.py         # -> dist/aivideo-agent.exe
```
Chạy exe (đặt biến môi trường, kèm thư mục plugins):
```bash
set PLUGINS_DIR=C:\AIVideoPlatform\plugins
set BACKEND_WS_URL=ws://localhost:8000/ws/agent
set AGENT_TOKEN=change-me-agent-token
dist\aivideo-agent.exe
```

Cấu hình agent: xem `agent/.env.example` (`DATA_DIR`, `CAPACITY`, `WATCH_DEBOUNCE_MS`, `PLUGINS_DIR`...).

---

## 4. Plugin (External App adapter)

Mỗi plugin nằm trong `plugins/<name>/` gồm `manifest.yaml` + `adapter.py` + `config.schema.json` + `README.md` (SPEC 08).

- **Agent** nạp plugin từ `PLUGINS_DIR` (hoặc `plugins/` cạnh mã nguồn) — đăng ký capability.
- **Backend** đồng bộ plugin vào registry lúc khởi động; xem/bật/tắt ở trang **Plugin Manager**.
- Plugin có sẵn: `ffmpeg` (video.ffmpeg), `yt_dlp` (media.download), `chrome` (web.cdp). Yêu cầu app tương ứng cài sẵn (FFmpeg trong PATH, yt-dlp, Google Chrome).
- Thêm plugin mới: tạo thư mục mới theo cấu trúc trên — **không sửa mã lõi** (SPEC 08 §1).

---

## 5. Deploy Frontend lên GitHub Pages

- Workflow `.github/workflows/frontend-pages.yml` tự build (base = `/<tên-repo>/`) và deploy khi push `main`.
- Bật **Settings → Pages → Source: GitHub Actions** trong repo.
- `404.html` (bản sao `index.html`) đảm bảo refresh ở mọi route hoạt động (SPA fallback).
- Trang web (Pages) trỏ tới backend self-host qua **Settings → API Base URL** (nhập URL backend của bạn).

---

## 6. Kiểm thử nhanh (smoke)

```bash
# Backend + Agent
cd backend && uvicorn app.main:app --port 8000      # cửa sổ 1
cd agent && python -m agent.main                     # cửa sổ 2
# E2E thật (cần FFmpeg trong PATH)
cd backend && RUN_E2E=1 pytest tests/e2e -q
```

Toàn bộ test: `cd backend && pytest -q` · `cd agent && pytest -q` · `cd frontend && npm run lint && npm run build`.
