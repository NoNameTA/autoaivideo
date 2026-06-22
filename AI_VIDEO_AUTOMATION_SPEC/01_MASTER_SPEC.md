# 01 — MASTER SPEC

> **Sản phẩm:** AI Video Platform V2 — Nền tảng tự động hoá sản xuất video AI hàng loạt (bulk).
> **Phiên bản tài liệu:** 2.0.0 — Khởi tạo lại toàn bộ (clean rewrite).
> **Ngày:** 2026-06-22
> **Trạng thái:** Spec gốc (source of truth). Mọi file khác trong bộ này phải nhất quán với file này.

---

## 1. Mục tiêu sản phẩm

AI Video Platform V2 cho phép một người dùng (hoặc một nhóm nhỏ) **sản xuất hàng loạt video** bằng cách điều phối các **công cụ AI miễn phí** (sinh ảnh, sinh video, text-to-speech, dựng/ghép video) một cách tự động, có hàng đợi (queue), có theo dõi tiến độ thời gian thực, và có thể mở rộng bằng plugin.

Khác biệt cốt lõi so với các công cụ rời rạc:

1. **Điều phối tập trung** — một nơi quản lý kịch bản → tài nguyên → render → xuất bản.
2. **Tự động hoá ứng dụng ngoài** — Desktop Agent điều khiển trình duyệt/app ngoài (qua CDP và UI automation) để dùng các dịch vụ AI miễn phí mà không có API chính thức.
3. **Bulk-first** — thiết kế cho 10–1000 video/lô, không phải 1 video thủ công.
4. **Free-only** — chỉ dùng phần mềm/dịch vụ miễn phí (xem `14_FREE_SOFTWARE_POLICY.md`).
5. **Plugin SDK** — thêm nguồn AI mới mà không sửa lõi (xem `08_PLUGIN_SDK.md`).

## 2. Phạm vi (Scope)

### Trong phạm vi (In scope)
- Quản lý **Project** (dự án) → **Batch** (lô) → **Job** (công việc đơn) → **Step** (bước).
- Hàng đợi tác vụ với retry, ưu tiên, giới hạn đồng thời.
- Desktop Agent điều khiển ứng dụng ngoài.
- Frontend dashboard (web, Vite) để cấu hình, theo dõi, xem kết quả.
- Backend API (FastAPI) làm bộ não điều phối.
- Lưu trữ file theo cấu trúc chuẩn (xem `07_FILE_SYSTEM_SPEC.md`).
- CSDL trạng thái (SQLite mặc định, Postgres tùy chọn).
- Plugin/adapter cho từng "External Application".

### Ngoài phạm vi (Out of scope) cho V2.0
- Multi-tenant SaaS công khai (chỉ self-host / 1 người dùng + token).
- Thanh toán, billing.
- Mobile app native.
- Tự huấn luyện model AI.

## 3. Người dùng & vai trò

| Vai trò | Mô tả | Quyền |
|--------|------|------|
| **Owner** | Chủ nền tảng, self-host | Toàn quyền |
| **Operator** | Người vận hành tạo batch | Tạo/chạy job, xem log |
| **Agent (máy)** | Tiến trình Desktop Agent | Nhận lệnh, báo trạng thái |

V2.0 mặc định single-user (Owner). RBAC chi tiết: xem `11_SECURITY_SPEC.md`.

## 4. Kiến trúc tổng quan (tóm tắt)

```
┌─────────────┐   WebSocket/REST   ┌──────────────┐   WebSocket   ┌───────────────┐
│  Frontend   │ ◄────────────────► │   Backend    │ ◄───────────► │ Desktop Agent │
│ (Vite/React)│                    │  (FastAPI)   │               │   (Python)    │
└─────────────┘                    └──────┬───────┘               └───────┬───────┘
                                          │                               │ CDP / UI automation
                                   ┌──────▼───────┐               ┌───────▼───────┐
                                   │   Database   │               │  External Apps │
                                   │ SQLite/PG    │               │ (browser/app)  │
                                   └──────────────┘               └───────────────┘
```

Chi tiết: `02_PROJECT_ARCHITECTURE.md`.

## 5. Khái niệm dữ liệu cốt lõi

- **Project**: một chiến dịch/nội dung (vd: "Kênh review phim"). Chứa cấu hình mặc định + nhiều Batch.
- **Batch**: một lô sản xuất (vd: "20 video tuần này"). Sinh ra N Job.
- **Job**: 1 video đầu ra. Gồm chuỗi **Step** (script → voice → image → video → merge → export).
- **Step**: 1 hành động đơn nguyên do 1 plugin/adapter thực hiện.
- **Asset**: file sinh ra (audio, image, clip, video cuối).
- **Plugin/Adapter**: trình điều khiển một External Application.

Sơ đồ quan hệ đầy đủ: `10_DATABASE_SPEC.md`.

## 6. Luồng end-to-end (happy path)

1. Operator tạo Project, chọn template pipeline.
2. Operator nhập danh sách input (CSV/biểu mẫu) → tạo Batch → N Job ở trạng thái `queued`.
3. Backend đẩy từng Step vào queue, phân phối tới Desktop Agent phù hợp.
4. Agent mở External App (vd trình tạo ảnh AI miễn phí), thực hiện, tải asset về thư mục chuẩn, báo `step.completed`.
5. Backend chạy Step kế tiếp đến khi Job `completed`.
6. Frontend hiển thị tiến độ realtime; Operator xem/duyệt/tải video cuối.

## 7. Yêu cầu phi chức năng

| Tiêu chí | Mục tiêu V2.0 |
|---------|---------------|
| Throughput | ≥ 50 job/ngày trên 1 máy agent |
| Đồng thời | Cấu hình được, mặc định 2 step song song/agent |
| Khôi phục | Job dở dang resume được sau crash |
| Độ trễ UI | Cập nhật trạng thái < 1s qua WebSocket |
| Cài đặt | `docker compose up` hoặc script 1 lệnh |
| Chi phí | 0đ phần mềm (free-only) |

## 8. Bộ tài liệu (Index)

| File | Nội dung |
|------|---------|
| 01_MASTER_SPEC | Tổng quan, scope, khái niệm (file này) |
| 02_PROJECT_ARCHITECTURE | Kiến trúc kỹ thuật, module, luồng dữ liệu |
| 03_FRONTEND_SPEC | Vite/React app, route, component, state |
| 04_BACKEND_SPEC | FastAPI, service, queue, orchestrator |
| 05_DESKTOP_AGENT_SPEC | Agent điều khiển app ngoài |
| 06_EXTERNAL_APPLICATION_SPEC | Chuẩn tích hợp app/dịch vụ ngoài |
| 07_FILE_SYSTEM_SPEC | Cấu trúc thư mục, đặt tên file |
| 08_PLUGIN_SDK | API viết plugin/adapter |
| 09_COMMUNICATION_PROTOCOL | Định dạng message WS/REST |
| 10_DATABASE_SPEC | Schema, bảng, quan hệ, migration |
| 11_SECURITY_SPEC | Auth, secrets, sandbox, RBAC |
| 12_UI_UX_SPEC | Design system, màn hình, flow |
| 13_GITHUB_DEPLOYMENT | CI/CD, Pages, release |
| 14_FREE_SOFTWARE_POLICY | Quy định chỉ dùng phần mềm miễn phí |
| 15_TESTING_SPEC | Chiến lược test, coverage |
| 16_TASK_ROADMAP | Lộ trình 9 giai đoạn |
| 17_CHANGELOG | Lịch sử thay đổi |
| 18_DEVELOPMENT_RULES | Quy tắc code, commit, review |

## 9. Nguyên tắc bất biến (Invariants)

1. Lõi không bao giờ phụ thuộc một External App cụ thể — chỉ qua interface plugin.
2. Mọi thao tác phá huỷ phải idempotent & có log.
3. Không hardcode secret trong repo.
4. Trạng thái thật nằm ở Database; file system là asset; frontend chỉ là view.
5. Chỉ dùng phần mềm miễn phí (xem `14`).
