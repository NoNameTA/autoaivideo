# 15 — TESTING SPEC

> Chiến lược kiểm thử cho backend, frontend, agent, plugin.

---

## 1. Tầng kiểm thử (test pyramid)

| Tầng | Phạm vi | Công cụ |
|------|--------|--------|
| Unit | hàm/service đơn lẻ | pytest (BE/agent), vitest (FE) |
| Contract | plugin/adapter, API schema | pytest + JSON Schema |
| Integration | orchestrator + DB + queue | pytest + SQLite tạm |
| E2E | luồng tạo batch → job hoàn tất (mock adapter) | pytest/Playwright |

## 2. Backend

- `pytest` + `pytest-asyncio`. DB test: SQLite in-memory/temp, migration thật.
- Test orchestrator: máy trạng thái step (assign→running→completed, retry, timeout requeue).
- Test API: TestClient (httpx ASGI), kiểm tra schema response & lỗi (`09 §6`).
- Coverage mục tiêu ≥ 80% core (orchestrator, services).

## 3. Plugin contract test

Mỗi plugin phải pass bộ test chuẩn do SDK cung cấp:
- `validate_config` chấp nhận/khước từ đúng theo schema.
- `prepare/run/collect/cleanup` gọi được với **mock driver**.
- Phân loại lỗi đúng (`TransientError`/`PermanentError`).
- Manifest hợp lệ + `free: true` (xem `14`).

## 4. Agent

- Mock WebSocket server: kiểm tra register, heartbeat, nhận assign, báo completed/failed, reconnect.
- Driver test với app giả lập (page tĩnh cho CDP; cửa sổ giả cho UIA nếu khả thi) — phần phụ thuộc OS có thể đánh dấu skip ngoài Windows.

## 5. Frontend

- `vitest` + Testing Library: component (JobGrid, StepTimeline, PluginConfigForm sinh từ schema).
- Mock WS/REST (msw) để test cập nhật realtime.
- E2E tuỳ chọn: Playwright chạy app + backend mock.

## 6. Dữ liệu test & fixtures

- Factory tạo Project/Batch/Job/Step.
- Pipeline mẫu dùng adapter "echo/mock" (không gọi app ngoài thật) cho integration/E2E.

## 7. CI gate (xem `13`)

- PR phải pass: lint (ruff/eslint), unit, contract, build.
- Block merge nếu coverage core giảm dưới ngưỡng.
- `pip-audit`/`npm audit` không có lỗ hổng high/critical.

## 8. Kiểm thử thủ công (smoke)

Trước release tag:
- [ ] `docker compose up` chạy được.
- [ ] Tạo project → batch 3 job (mock adapter) → tất cả completed.
- [ ] Agent thật kết nối + chạy 1 step web thật.
- [ ] Retry job failed hoạt động.
- [ ] Frontend Pages build trỏ đúng backend.
