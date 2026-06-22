# 16 — TASK ROADMAP

> Lộ trình 9 giai đoạn (GĐ). Mỗi GĐ có tiêu chí hoàn thành (DoD). Tham chiếu toàn bộ spec.

---

## Tổng quan 9 giai đoạn

| GĐ | Tên | Mục tiêu | Trạng thái |
|----|-----|---------|-----------|
| 1 | Nền móng | Repo, skeleton BE/FE/Agent, CI | ✅ Done (theo memory) |
| 2 | Mô hình dữ liệu & API | DB schema, ORM, REST CRUD | ⬜ |
| 3 | Orchestrator & Queue | Engine, durable queue, máy trạng thái | ⬜ |
| 4 | Agent & Driver | WS agent, CDP/UIA driver, 1 adapter mẫu | ⬜ |
| 5 | Plugin SDK | Base adapter, loader, contract test | ⬜ |
| 6 | Frontend MVP | Dashboard, batch, job detail realtime | ⬜ |
| 7 | Pipeline đầy đủ | Template faceless end-to-end (mock→thật) | ⬜ |
| 8 | Bảo mật & độ tin cậy | Auth, secret store, retry/resume, audit | ⬜ |
| 9 | Đóng gói & phát hành | Docker, Pages, agent exe, docs, release | ⬜ |

---

## GĐ1 — Nền móng ✅
- Monorepo (`backend/frontend/agent/plugins`), config, lint, CI `ci.yml`.
- **DoD**: CI xanh, app chạy "hello" BE+FE.

## GĐ2 — Mô hình dữ liệu & API
- Bảng theo `10`, Alembic migration, ORM.
- REST CRUD projects/batches/jobs (`04 §2`), Pydantic schema.
- **DoD**: tạo project→batch→job qua API, lưu DB; test API pass.

## GĐ3 — Orchestrator & Queue
- `job_queue` durable, dispatcher, máy trạng thái step (`04 §4`), retry/backoff, resume sau restart.
- **DoD**: chạy pipeline mock end-to-end trong 1 process; integration test trạng thái + retry + timeout requeue.

## GĐ4 — Agent & Driver
- WS `/ws/agent`, register/heartbeat (`09 §4`), runner.
- CDP driver + UIA driver tối thiểu; 1 adapter thật (vd `cli-process` ffmpeg/whisper).
- **DoD**: agent nhận step, chạy adapter cli thật, báo completed; reconnect hoạt động.

## GĐ5 — Plugin SDK
- Base `Adapter`, StepContext, loader/registry, JSON Schema config (`08`).
- Contract test framework.
- **DoD**: thêm 1 plugin mới không sửa lõi; contract test pass; `free` gate (`14`).

## GĐ6 — Frontend MVP
- Routes `03 §3`, WS realtime, JobGrid/StepTimeline/AssetPreview, PluginConfigForm.
- Design system `12`.
- **DoD**: theo dõi batch realtime, retry/cancel từ UI, xem asset.

## GĐ7 — Pipeline đầy đủ
- Template "faceless_v1" (`02 §4`): script→voice→images→subtitle→assemble→export.
- Ít nhất 1 External App web thật qua CDP (`06`).
- **DoD**: tạo batch → ra video `final.mp4` thật end-to-end.

## GĐ8 — Bảo mật & độ tin cậy
- Auth token owner/agent, secret store mã hoá, redaction log (`11`).
- Resume/at-least-once + dedupe (`09 §7`).
- **DoD**: checklist bảo mật `11 §9` pass; crash giữa chừng → resume đúng.

## GĐ9 — Đóng gói & phát hành
- Docker compose, GitHub Pages, agent exe, README/docs, `release.yml`.
- **DoD**: `docker compose up` + agent exe chạy được trên máy sạch; release `v2.0.0` có artefact; smoke test `15 §8` pass.

---

## Nguyên tắc thực thi
- Mỗi GĐ là một (hoặc vài) PR có test + cập nhật `17_CHANGELOG.md`.
- Không nhảy GĐ khi DoD chưa đạt.
- Cập nhật cột "Trạng thái" ở bảng trên mỗi khi xong GĐ.
