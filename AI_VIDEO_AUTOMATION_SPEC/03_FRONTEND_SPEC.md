# 03 — FRONTEND SPEC

> Web dashboard. Stack: Vite + React 18 + TypeScript + Tailwind CSS + Zustand. Theme: tham chiếu `12_UI_UX_SPEC.md`.

---

## 1. Mục tiêu

Giao diện để: cấu hình Project/Pipeline, nạp input hàng loạt, theo dõi Batch/Job realtime, duyệt & tải kết quả, quản lý Agent và Plugin.

## 2. Công nghệ & cấu trúc

```
frontend/src/
├── pages/         # route-level
├── components/    # tái sử dụng
├── store/         # Zustand slices (projects, jobs, agents, ws)
├── api/           # rest.ts (fetch), ws.ts (WebSocket client)
├── hooks/
├── lib/           # format, validators
└── main.tsx
```

- Build: Vite. Output tĩnh → deploy GitHub Pages (xem `13`).
- State server-cache: TanStack Query cho REST; Zustand cho realtime/WS state.
- Form: React Hook Form + Zod.

## 3. Routes / Màn hình

| Route | Màn hình | Mô tả |
|-------|----------|------|
| `/` | Dashboard | Tổng quan: job đang chạy, throughput, cảnh báo |
| `/projects` | Danh sách Project | CRUD project |
| `/projects/:id` | Chi tiết Project | Cấu hình pipeline mặc định, batch |
| `/projects/:id/batches/new` | Tạo Batch | Nạp input CSV/biểu mẫu, preview job sinh ra |
| `/batches/:id` | Theo dõi Batch | Lưới Job + trạng thái realtime |
| `/jobs/:id` | Chi tiết Job | Timeline Step, log, asset, nút retry/cancel |
| `/agents` | Agent | Trạng thái agent, capability, heartbeat |
| `/plugins` | Plugin | Cài/bật/tắt plugin, xem schema config |
| `/settings` | Cài đặt | Token, đường dẫn data, theme |

## 4. State realtime

`ws.ts` mở 1 WebSocket tới `/ws`, đăng ký kênh theo `batch_id`/`job_id` đang xem. Message (xem `09`) cập nhật Zustand store → component re-render. Có auto-reconnect + backoff; khi mất kết nối hiển thị banner "Đang kết nối lại".

## 5. Component chính

- `JobGrid` — lưới job, màu theo trạng thái, virtualized cho batch lớn.
- `StepTimeline` — timeline ngang các step + thời lượng + log inline.
- `AssetPreview` — xem trước ảnh/audio/video (player), tải xuống.
- `InputImporter` — upload CSV, map cột → biến pipeline, validate, preview.
- `AgentCard` — trạng thái agent + capability badge.
- `PluginConfigForm` — form sinh động từ JSON Schema của plugin (`08`).
- `PipelineEditor` — kéo-thả/cấu hình step (V2.1+, V2.0 chỉ chọn template).

## 6. Xử lý lỗi & trạng thái rỗng

- Mọi list có empty-state hướng dẫn hành động kế tiếp.
- Lỗi API → toast + nút retry; lỗi WS → banner.
- Job `failed` → hiển thị lý do + log + nút "Retry step".

## 7. Hiệu năng

- Virtualize danh sách > 100 dòng.
- Debounce filter/search.
- Lazy-load page bằng `React.lazy`.
- Bundle < 300KB gzip cho route đầu.

## 8. Accessibility & i18n

- Mặc định tiếng Việt; cấu trúc i18n (key-based) để thêm ngôn ngữ.
- Tuân thủ WCAG AA cơ bản: focus ring, aria-label, tương phản.
