# AI Video Platform V2

Nền tảng tự động hoá sản xuất video AI hàng loạt. Tài liệu đặc tả chính thức: [`AI_VIDEO_AUTOMATION_SPEC/`](AI_VIDEO_AUTOMATION_SPEC/01_MASTER_SPEC.md).

## Kiến trúc (SPEC 02)

```
Frontend (Vite/React) ⇄ Backend (FastAPI) ⇄ Desktop Agent (Python) ⇄ External Apps (plugin)
```

## Cấu trúc repo

| Thư mục | Mô tả |
|---------|------|
| `backend/` | FastAPI — API, orchestrator, queue, plugin host |
| `frontend/` | Vite + React + TS + Tailwind dashboard |
| `agent/` | Desktop Agent điều khiển app ngoài |
| `plugins/` | Plugin/adapter cho External Apps |
| `data/` | File system runtime (gitignored) |
| `AI_VIDEO_AUTOMATION_SPEC/` | Bộ 18 tài liệu đặc tả |
| `.github/workflows/` | CI/CD |

## Yêu cầu môi trường

- **Python** 3.11+
- **Node.js** 18+ (đã test v24)
- **git**, (tuỳ chọn) Docker

## Chạy nhanh (dev)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/health
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # build tĩnh -> dist/
```

### Agent
```bash
cd agent
pip install -r requirements.txt
python -m agent.main
```

## Lộ trình

Xem [`AI_VIDEO_AUTOMATION_SPEC/16_TASK_ROADMAP.md`](AI_VIDEO_AUTOMATION_SPEC/16_TASK_ROADMAP.md) và [`CHANGELOG.md`](CHANGELOG.md).

## Giấy phép

Free-software only — xem [`AI_VIDEO_AUTOMATION_SPEC/14_FREE_SOFTWARE_POLICY.md`](AI_VIDEO_AUTOMATION_SPEC/14_FREE_SOFTWARE_POLICY.md).
