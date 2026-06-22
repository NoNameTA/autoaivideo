# 06 — EXTERNAL APPLICATION SPEC

> Chuẩn tích hợp một "ứng dụng/dịch vụ ngoài" (External App) mà Agent điều khiển. Mỗi External App được bọc bởi một Adapter (xem `08`).

---

## 1. Định nghĩa

**External Application** = bất kỳ công cụ ngoài lõi nền tảng được dùng để thực hiện một Step:
- Web app (trình tạo ảnh/video AI miễn phí, TTS online) → điều khiển qua **CDP**.
- Desktop app (trình dựng video, ffmpeg GUI) → điều khiển qua **UI automation** hoặc CLI.
- CLI/local tool (ffmpeg, whisper.cpp) → gọi trực tiếp process.

⚠️ Mọi External App phải **miễn phí** và tuân thủ `14_FREE_SOFTWARE_POLICY.md`, đồng thời tôn trọng ToS của dịch vụ.

## 2. Phân loại tích hợp

| Loại | Cơ chế | Ví dụ |
|------|--------|------|
| `web-cdp` | Playwright/CDP điều khiển trình duyệt | trình sinh ảnh AI web miễn phí |
| `desktop-uia` | UI automation cửa sổ native | app dựng video desktop |
| `cli-process` | Spawn process + args | ffmpeg, whisper.cpp, yt-dlp |
| `local-http` | App ngoài expose HTTP localhost | server TTS/LLM chạy máy (vd local model) |

## 3. Hợp đồng (Contract) của một External App integration

Mỗi integration phải khai báo:
```yaml
name: image.free_gen
type: web-cdp
version: 1.0.0
capability: image.free_gen          # khớp capability agent
free: true                          # bắt buộc true
inputs:  { prompt: string, count: int }
outputs: { images: file[] }
config_schema: ...                  # JSON Schema (token, url, tuỳ chọn)
selectors: ...                      # selector/bước thao tác (cho web-cdp)
healthcheck: ...                    # cách kiểm tra app sẵn sàng
```

## 4. Vòng đời tương tác (web-cdp ví dụ)

1. `prepare`: mở URL, đăng nhập nếu cần (dùng profile lưu phiên), kiểm tra sẵn sàng.
2. `run`: nhập prompt → submit → chờ kết quả (poll/observe DOM) → xử lý rate limit/captcha (báo lỗi `Permanent` nếu chặn).
3. `collect`: tải file kết quả về `DATA_DIR` theo `07`.
4. `cleanup`: đóng tab/context.

## 5. Xử lý tình huống xấu

| Tình huống | Xử lý |
|-----------|------|
| Rate limit | đợi/backoff → nếu vượt ngưỡng: `TransientError` |
| Đổi giao diện (selector hỏng) | `PermanentError` + screenshot → cần cập nhật adapter |
| Captcha/đăng nhập lại | `PermanentError`, báo cần can thiệp người dùng |
| Mạng lỗi | `TransientError`, retry |

## 6. Quản lý phiên & xác thực app ngoài

- Lưu profile trình duyệt/persisted context riêng cho mỗi External App (không commit vào repo).
- Token/cookie nhạy cảm xử lý theo `11_SECURITY_SPEC.md`.

## 7. Danh mục External App (registry)

Mỗi External App có 1 file định nghĩa trong `plugins/<name>/manifest.yaml` + code adapter. Lõi không biết tên cụ thể — chỉ biết capability. Thêm app mới = thêm plugin (xem `08`), không sửa lõi.

## 8. Tuân thủ

- Chỉ tích hợp dịch vụ cho phép sử dụng tự động/miễn phí theo ToS.
- Ghi rõ nguồn & giấy phép trong manifest (`license`, `source_url`).
