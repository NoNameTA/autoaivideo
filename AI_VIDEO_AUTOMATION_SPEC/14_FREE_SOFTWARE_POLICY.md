# 14 — FREE SOFTWARE POLICY

> Ràng buộc bất biến: nền tảng và mọi tích hợp chỉ dùng phần mềm/dịch vụ MIỄN PHÍ. Đây là invariant (`01 §9`).

---

## 1. Nguyên tắc

1. **0đ chi phí phần mềm**: không dùng công cụ/dịch vụ trả phí bắt buộc, không subscription, không API tính phí.
2. **Ưu tiên mã nguồn mở** (OSI license) khi có thể.
3. **Tôn trọng ToS**: tự động hoá chỉ với dịch vụ cho phép; không lách giới hạn trả phí.
4. **Self-host được**: ưu tiên công cụ chạy local (ffmpeg, whisper.cpp, model local).

## 2. Phân loại được phép

| Loại | Được dùng? | Điều kiện |
|------|-----------|----------|
| OSS local (ffmpeg, whisper.cpp, yt-dlp) | ✅ | giấy phép tương thích |
| Web app miễn phí có free tier | ✅ | trong hạn miễn phí + ToS cho phép tự động |
| Model AI local (chạy máy) | ✅ | giấy phép cho dùng |
| API trả phí | ❌ | trừ khi có free tier đủ dùng & hợp lệ |
| Phần mềm crack / lách license | ❌ tuyệt đối | |
| Dịch vụ cấm bot/automation | ❌ | vi phạm ToS |

## 3. Bắt buộc trong manifest plugin

Mỗi plugin/External App (`06`,`08`) phải khai:
```yaml
free: true            # CI xử lý theo policy (xem §4)
commercial: false     # true = dịch vụ trả phí (vd OpenAI/Anthropic) — AP2
license: <SPDX>       # vd MIT, Apache-2.0, GPL-3.0
source_url: <link>
tos_url: <link>       # ToS dịch vụ (nếu web/cloud)
automation_allowed: true   # xác nhận ToS cho phép
```

> Với **Cloud Adapter** (`cloud-api`), `free`/`commercial` lấy theo **Provider Framework metadata**
> (SPEC 06 §9.8) — khai báo trung lập, **không hard-code** trong CI theo từng provider.

## 4. Kiểm soát tự động (CI gate — policy-driven, AP2)

- CI đọc **policy cấu hình** (allowlist license + chế độ với `free:false`/`commercial:true`), **không**
  hard-code tên provider:
  - `free: false` / `commercial: true` → theo policy: **cảnh báo** (cho phép owner bật có chủ đích §6)
    hoặc **chặn** (chế độ free-only nghiêm ngặt). Mặc định: chặn trừ khi override có lý do (§6).
  - thiếu `license` → **fail build**.
- Danh sách license cấm (vd license độc quyền không cho phân phối) → fail.
- Liệt kê dependency: chỉ license trong allowlist (MIT/BSD/Apache/MPL/LGPL/GPL...) qua `pip-licenses`/`license-checker`.

## 5. Giấy phép dự án

- Mã nền tảng phát hành giấy phép mở (đề xuất **MIT** hoặc **Apache-2.0**).
- Tương thích copyleft: nếu link thư viện GPL, cân nhắc ảnh hưởng phát hành.

## 6. Khi không có lựa chọn miễn phí

- Ưu tiên giải pháp local/OSS thay thế (vd TTS local thay TTS trả phí).
- Nếu một tính năng bắt buộc cần dịch vụ trả phí → tính năng đó **không** vào lõi; chỉ có thể là plugin tuỳ chọn người dùng tự bật và tự chịu trách nhiệm, và phải đánh dấu rõ `free: false` (mặc định CI chặn — cần override thủ công có lý do).

## 7. Trách nhiệm người dùng

- Người vận hành chịu trách nhiệm tuân thủ ToS của dịch vụ ngoài tại khu vực của họ.
- Nền tảng cung cấp công cụ; không khuyến khích vi phạm điều khoản bên thứ ba.
