# 17 — CHANGELOG

> Định dạng theo [Keep a Changelog](https://keepachangelog.com/). Phiên bản theo SemVer.

---

## [Unreleased]
### Added
- (đang phát triển theo `16_TASK_ROADMAP.md`)

---

## [2.0.0-spec] - 2026-06-22
### Added
- Khởi tạo lại **toàn bộ bộ spec** AI Video Platform V2 (clean rewrite, 18 tài liệu).
- Định nghĩa kiến trúc 4 thành phần: Frontend (Vite), Backend (FastAPI), Desktop Agent (Python), External Apps qua adapter.
- Mô hình dữ liệu Project → Batch → Job → Step → Asset.
- Orchestrator + durable queue + máy trạng thái step + retry/resume.
- Plugin SDK (base Adapter, StepContext, JSON Schema config).
- Giao thức truyền thông WS/REST (envelope, ack, reconnect).
- Schema CSDL (SQLite mặc định, Postgres tuỳ chọn).
- Chính sách Free-Software (CI gate `free: true`).
- Lộ trình 9 giai đoạn với DoD.

### Removed
- Gỡ bỏ toàn bộ dữ liệu/dự án cũ tại `C:\BulkAuto` (đã có trên GitHub remote `TranQA28/bulk-video-studio-automation`).

### Notes
- GĐ1 (Nền móng) ghi nhận đã hoàn thành theo trạng thái dự án trước đó; các GĐ còn lại ⬜.

---

## Quy ước ghi changelog
- Nhóm: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- Mỗi release gắn ngày `YYYY-MM-DD` và tag git `vX.Y.Z` (`13 §7`).
- Mục `[Unreleased]` gom thay đổi chờ phát hành.
