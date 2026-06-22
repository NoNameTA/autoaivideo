# 05 — DESKTOP AGENT SPEC

> Tiến trình chạy trên máy người dùng, điều khiển ứng dụng ngoài để thực thi Step. Python. Tham chiếu `06`, `08`, `09`.

---

## 1. Vai trò

Backend không tự "bấm nút" trên app ngoài — Desktop Agent làm việc đó. Agent:
1. Kết nối WebSocket tới backend `/ws/agent`, đăng ký `capabilities`.
2. Nhận `step.assign`, chạy adapter tương ứng (CDP hoặc UI automation).
3. Tải asset về thư mục chuẩn (`07`), báo `step.progress/completed/failed`.
4. Gửi heartbeat định kỳ.

## 2. Cấu trúc

```
agent/agent/
├── main.py          # bootstrap, đọc config, kết nối WS
├── connection.py    # WS client + reconnect + envelope
├── runner.py        # nhận step → resolve adapter → chạy → báo kết quả
├── drivers/
│   ├── cdp.py       # Playwright/CDP cho app web (Chromium)
│   └── uia.py       # pywinauto/UI automation cho app desktop
├── adapters/        # impl phía agent của từng External App
├── fs.py            # ghi asset đúng chuẩn 07
└── config.py
```

## 3. Đăng ký & capability

Khi kết nối, agent gửi:
```json
{ "type": "agent.register",
  "data": { "agent_id": "win-pc-01", "version": "2.0.0",
            "capabilities": ["llm.free_chat","tts.free_tts","video.ffmpeg"],
            "capacity": 2, "os": "windows" } }
```
Dispatcher route step chỉ tới agent có capability khớp.

## 4. Drivers

### CDP Driver (web app)
- Dùng Playwright kết nối Chromium (cùng kỹ thuật CDP/`window.api` đã dùng ở dự án trước).
- Có thể attach vào Chrome đang mở (debug port) hoặc khởi chạy context riêng.
- Cung cấp API: `goto`, `click`, `type`, `wait_for`, `eval`, `download`, `screenshot`.

### UI Automation Driver (desktop app)
- pywinauto (Windows) điều khiển cửa sổ native: focus, click control, gõ phím, đọc trạng thái.
- Dùng khi app không có giao diện web.

## 5. Vòng đời thực thi Step

```
recv step.assign
  → ack (step.ack)
  → adapter.prepare(inputs, config)
  → adapter.run(driver) ──progress──► gửi step.progress (%)
  → adapter.collect() → fs.save_asset()
  → step.completed { assets: [...] }
trên lỗi:
  → phân loại Transient/Permanent → step.failed { error, retryable }
```

- Heartbeat mỗi `heartbeat_interval` (mặc định 30s).
- Nếu mất WS: dừng nhận mới, hoàn tất step đang chạy nếu được, reconnect, báo lại trạng thái.

## 6. Cô lập & an toàn

- Mỗi step web chạy trong browser context riêng (cookie/profile tách biệt) khi cần.
- Không lưu secret lên đĩa dạng plain (xem `11`).
- Giới hạn thời gian mỗi step (`step_timeout`) để tránh treo.
- Chụp screenshot khi lỗi để debug (lưu vào asset/log dir).

## 7. Cấu hình agent

```
BACKEND_WS_URL=ws://localhost:8000/ws/agent
AGENT_ID=win-pc-01
AGENT_TOKEN=...                 # xác thực, xem 11
DATA_DIR=C:\AIVideoPlatform\data
CHROME_DEBUG_PORT=9222
HEARTBEAT_INTERVAL=30
STEP_TIMEOUT=600
```

## 8. Cài đặt & chạy

- Chạy như script Python hoặc đóng gói exe (PyInstaller) cho người không rành kỹ thuật.
- Tự kiểm tra phụ thuộc (Chromium, ffmpeg) khi khởi động; báo thiếu rõ ràng.
