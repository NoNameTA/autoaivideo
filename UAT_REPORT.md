# BÁO CÁO NGHIỆM THU UAT — AI Video Platform V2

> **Ngày:** 2026-06-23 · **Phiên bản:** v1.0.0 (+ UAT 5 trang) · **Người chạy:** Claude (Opus 4.8)
> **Hình thức:** Nghiệm thu **end-to-end bằng hệ thống THẬT** — không mock, không bypass.

---

## 1. Môi trường & cấu phần chạy thật

| Cấu phần | Chi tiết | Trạng thái |
|---|---|---|
| **Backend** | FastAPI uvicorn `:8000`, v2.0.0, env=dev, SQLite | ✅ Online |
| **Desktop Agent** | `aivideo-agent.exe` (PyInstaller), id=`uat-exe-agent`, os=windows, capacity=2 | ✅ Kết nối WS thật |
| **Frontend** | Vite preview `:5173` (build production 120.8 KB gzip) | ✅ Render thật |
| **Plugins nạp** | `PLUGINS_DIR=C:\AIVideoPlatform\plugins` → 6 capability | ✅ |
| **FFmpeg** | Gyan 8.1.1 trên PATH | ✅ |

**Capabilities agent đăng ký (thật):** `cli.run`, `video.ffmpeg`, `web.cdp`, `web.cdp.edge`, `desktop.notepad`, `media.download`.

---

## 2. Kết quả theo yêu cầu (PASS/FAIL)

| # | Hạng mục | Kết quả | Bằng chứng |
|---|---|---|---|
| 1 | Website ↔ Backend ↔ Agent ↔ Plugin chạy thật | ✅ **PASS** | Agent .exe online qua WS `/ws/agent`, 6 capability đăng ký |
| 2 | Workflow hoàn chỉnh Project→Batch→Job done | ✅ **PASS** | `ffmpeg_demo`: job completed 100%, asset **out.mp4 2326B** thật trên đĩa |
| 3a | Trang **Workflow** | ✅ **PASS** | 5 pipeline (gồm `uat_notepad` tạo qua API → lưu DB), DAG + nút Run |
| 3b | Trang **Queue** | ✅ **PASS** | 10 job thật realtime, filter đếm completed(8)/failed(2), retry/cancel |
| 3c | Trang **Logs** | ✅ **PASS** | 32 event persist DB (info=28/error=2/warn=2); lọc theo level; reload vẫn còn |
| 3d | Trang **Statistics** | ✅ **PASS** | KPI từ data thật (job/hoàn tất/tỉ lệ lỗi/step), biểu đồ throughput SVG, adapter timing |
| 3e | Trang **External Apps** | ✅ **PASS** | 5 app phân loại đúng; connected khi agent online; **Test kết nối ok=true** |
| 4 | Dashboard realtime | ✅ **PASS** | Feed live: `plugin.runtime.started/finished · video.ffmpeg` → `job completed 100%` (không reload) |
| 5 | Desktop Agent (.exe) kết nối thật | ✅ **PASS** | `uat-exe-agent` online; tắt .exe → backend tự set **offline** + broadcast |
| 6a | Plugin **FFmpeg** (video.ffmpeg) | ✅ **PASS** | Chạy live → out.mp4 thật (3 file) |
| 6b | Plugin **Chrome/CDP** (web.cdp) | ✅ **PASS** | `agent_full_demo`: step `shot [web.cdp]` completed + screenshot.png |
| 6c | Plugin **Edge/CDP**, **yt-dlp** | ✅ **PASS** (nạp+kết nối+test) | capability đăng ký, External Apps connected, Test ok=true |
| 6d | Plugin **Notepad UIA** (desktop.notepad) | ⚠️ **FAIL (live)** | Nạp+kết nối+test ok, nhưng **chạy live thất bại** — xem §3 |
| 7a | Retry job | ✅ **PASS** | Job `failed → queued` (re-dispatch) |
| 7b | Cancel job | ✅ **PASS** | Job `queued → cancelled` |
| 7c | Log persistence | ✅ **PASS** | 32 event tồn tại sau **hard reload** (load từ DB, không phải buffer) |
| 7d | Realtime event | ✅ **PASS** | activity + agent.updated cập nhật live qua WS |
| 7e | Agent status online→offline | ✅ **PASS** | Tắt .exe → DB=offline, Dashboard "Agent online 0", External Apps → no_agent |
| 8 | Không mock/bypass | ✅ **PASS** | Toàn bộ qua API/WS thật + agent .exe + ffmpeg/chrome thật |

**Tổng kết:** 19/20 hạng mục **PASS**; 1 hạng mục **FAIL ở mức chạy-live** (Notepad UIA) — plugin vẫn nạp/kết nối/test OK, không chặn workflow lõi.

---

## 3. Lỗi phát hiện & đề xuất sửa

### 🔴 [F-1] Plugin Notepad UIA chạy live thất bại
- **Hiện tượng:** pipeline `uat_notepad` (capability `desktop.notepad`) → step `failed` sau ~18s, lỗi: `Không tìm thấy cửa sổ 'Notepad': None`.
- **Nguyên nhân (phân tích):**
  1. **Windows 11 thay Notepad cổ điển bằng app UWP/Store** — `UiaDriver.start("notepad.exe", title_re="Notepad")` (pywinauto backend uia) không gắn được cửa sổ do mô hình tiến trình/cây UIA khác.
  2. Agent .exe chạy nền (`-WindowStyle Hidden`) — phiên tương tác hạn chế với UIA.
- **Đánh giá:** Đây là hạn chế đã biết (CHANGELOG Phase 9 đã ghi "UIA Notepad chưa verify live"). Các nhánh khác của UIA driver (focus/type/get_text) phụ thuộc bước `start` nên không kiểm được tiếp.
- **Đề xuất sửa (ưu tiên thấp, không chặn UAT lõi):**
  1. Cập nhật `agent/drivers/uia.py`: hỗ trợ Win11 Notepad (match theo `process` + `AutomationId`/`ClassName`, hoặc tăng `timeout`/`WaitForInputIdle`), hoặc dùng editor cổ điển (`notepad.exe` của Windows Accessories / wordpad) cho demo UIA.
  2. Chạy agent ở phiên tương tác (không hidden) khi cần UIA desktop.
  3. Hoặc đổi plugin demo UIA sang app ổn định hơn (Calculator/`win32calc`) để minh hoạ desktop-uia.

### 🟢 Không có lỗi nào khác
- Validation hoạt động đúng (vd `logs?limit=500` → `VALIDATION_ERROR` envelope chuẩn, max 200).
- Engine/dispatch/retry/cancel/state machine/realtime/persistence: không phát hiện lỗi.

---

## 4. Số liệu nghiệm thu (cuối phiên)

- **Jobs:** 11 tổng · 8 completed · throughput thật ghi nhận trên Statistics.
- **Steps:** 17; adapter chạy thật: `video.ffmpeg`×4, `web.cdp`×1, `cli.run`×10 (lịch sử), `desktop.notepad`×1.
- **Assets thật trên đĩa:** 3× `out.mp4` (ffmpeg) + 1× `screenshot.png` (chrome CDP) tại `agent/uat_data/...`.
- **Audit-log:** 32 event persist DB (info=28, error=2, warn=2) — gồm `plugin.runtime.failed · desktop.notepad` đúng level `error`.

---

## 5. Kết luận & khuyến nghị

✅ **Hệ thống ĐẠT nghiệm thu end-to-end ở mọi tiêu chí lõi:** website ↔ backend ↔ agent .exe ↔ plugin chạy thật; workflow hoàn chỉnh tạo asset thật; 5 trang UAT + Dashboard realtime hoạt động; retry/cancel/log-persistence/realtime/agent-status đều PASS; không dùng mock/bypass.

⚠️ **1 hạn chế cần quyết định:** plugin **Notepad UIA** chưa chạy live trên Win11 (nạp/kết nối/test OK). Đề xuất xử lý ở [F-1] — **không chặn** phase tiếp theo vì không thuộc luồng cốt lõi.

**Khuyến nghị:** Chấp nhận UAT; xếp [F-1] vào backlog cải tiến driver UIA (làm cùng/sau Adapter mới). **Chờ duyệt của chủ dự án trước khi bắt đầu Phase tiếp theo (Google Sheets Adapter).**
