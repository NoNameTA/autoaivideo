# 13 — GITHUB & DEPLOYMENT

> CI/CD bằng GitHub Actions. Frontend → GitHub Pages. Backend/Agent → release artefact + Docker.

---

## 1. Repo & nhánh

- Mặc định 1 monorepo: `backend/`, `frontend/`, `agent/`, `plugins/`, `AI_VIDEO_AUTOMATION_SPEC/`.
- Nhánh: `main` (ổn định), `dev` (tích hợp), feature `feat/*`, fix `fix/*`.
- PR bắt buộc qua CI + review (xem `18`).

## 2. GitHub Actions workflows

| Workflow | Trigger | Việc |
|----------|---------|------|
| `ci.yml` | push/PR | lint + test backend (pytest) + frontend (vitest) + plugin contract test |
| `frontend-pages.yml` | push `main` (frontend/**) | build Vite → deploy GitHub Pages |
| `release.yml` | tag `v*` | build Docker backend, đóng gói agent (PyInstaller), tạo GitHub Release |
| `audit.yml` | lịch tuần | `pip-audit`, `npm audit` |

### ci.yml (phác thảo)
```yaml
on: [push, pull_request]
jobs:
  backend:
    steps: [checkout, setup-python, pip install, ruff, pytest --cov]
  frontend:
    steps: [checkout, setup-node, npm ci, npm run lint, npm run test, npm run build]
  plugins:
    steps: [checkout, run plugin contract tests]
```

## 3. Frontend → GitHub Pages

- Build tĩnh `frontend/dist` → deploy Pages.
- `VITE_API_BASE` cấu hình qua secret/biến môi trường build (trỏ backend self-host).
- `base` trong `vite.config` đặt theo tên repo nếu dùng project pages.

## 4. Backend deploy

- Image Docker đa tầng (slim). `docker-compose.yml` gồm: backend, (tuỳ chọn) postgres, reverse proxy TLS.
- Cách chạy nhanh: `docker compose up -d`.
- Migration chạy lúc khởi động (entrypoint `alembic upgrade head`).

## 5. Agent phân phối

- `release.yml` build exe (Windows) bằng PyInstaller → đính kèm GitHub Release.
- Người dùng tải, đặt `AGENT_TOKEN` + `BACKEND_WS_URL`, chạy.

## 6. Secrets trong GitHub

- Dùng GitHub Encrypted Secrets cho deploy (không commit).
- Không build secret runtime của app ngoài vào artefact public.

## 7. Versioning & release

- SemVer. Tag `vX.Y.Z` → `release.yml`.
- `17_CHANGELOG.md` cập nhật mỗi release (Keep a Changelog).
- Release note tự sinh từ PR labels.

## 8. Môi trường

| Env | Mục đích |
|-----|---------|
| dev | local, SQLite, không TLS |
| staging | thử nghiệm, gần prod |
| prod | self-host, Postgres tuỳ chọn, TLS |
