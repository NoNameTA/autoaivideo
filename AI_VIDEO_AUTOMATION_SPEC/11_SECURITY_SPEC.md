# 11 — SECURITY SPEC

> Mô hình self-host, single-owner. Mục tiêu: bảo vệ token, secret, dữ liệu và kênh giao tiếp.

---

## 1. Mô hình mối đe doạ (tóm tắt)

| Tài sản | Đe doạ | Giảm thiểu |
|---------|--------|-----------|
| Token API/cookie app ngoài | rò rỉ qua repo/log | secret store, không log, .gitignore |
| Kênh WS/REST | nghe lén, giả mạo agent | token + TLS |
| Đĩa DATA_DIR | path traversal, ghi đè | validate path, chroot logic |
| Backend | truy cập trái phép | auth bắt buộc |

## 2. Xác thực & phân quyền

- **Frontend/Owner**: Bearer token (`AUTH_TOKEN`) hoặc login cấp JWT ngắn hạn (V2.1). Mọi REST/WS yêu cầu token.
- **Agent**: `AGENT_TOKEN` riêng (khác token người dùng); kênh `/ws/agent` chỉ chấp nhận token agent hợp lệ.
- RBAC: V2.0 chỉ Owner. Cấu trúc role để mở rộng Operator (chỉ chạy job, không sửa cấu hình).

## 3. Quản lý secret

- Secret (token, cookie, mật khẩu app ngoài) **không** lưu plaintext trong repo/DB plain.
- Lưu trong:
  - biến môi trường / file `.env` (gitignored), hoặc
  - secret store mã hoá (Fernet/AES với khoá từ `MASTER_KEY` env).
- Field config có `secret: true` (JSON Schema) → mã hoá khi lưu DB, ẩn khi trả về API (chỉ trả `***`).
- Profile trình duyệt (cookie phiên app ngoài) lưu ngoài repo, quyền hạn chế.

## 4. Bảo vệ kênh

- Production: bắt buộc `https`/`wss` (reverse proxy TLS, vd Caddy/Nginx).
- CORS: chỉ origin cấu hình (`CORS_ORIGINS`).
- Rate limit cơ bản trên API ghi.

## 5. An toàn file system

- Mọi đường dẫn từ input phải `os.path.realpath` + kiểm tra nằm trong `DATA_DIR` (chống `../`).
- Tên file sinh từ ID, không từ input thô.
- Upload asset: giới hạn size, kiểm tra mime/checksum.

## 6. Logging an toàn

- Không log token/cookie/secret (redaction filter).
- Log có `trace_id` để điều tra nhưng không chứa PII nhạy cảm.
- Screenshot lỗi có thể chứa thông tin — lưu trong DATA_DIR (gitignored), không gửi ra ngoài.

## 7. Phụ thuộc & cập nhật

- Pin phiên bản (`requirements.txt` / `package-lock.json`).
- Quét lỗ hổng: `pip-audit`, `npm audit` trong CI (`13`,`15`).
- Chỉ dùng phần mềm tuân thủ `14`.

## 8. Cô lập thực thi

- Agent chạy adapter với timeout; process CLI giới hạn quyền (không chạy quyền admin trừ khi cần).
- Browser context tách biệt giữa các External App.
- Không eval input người dùng như code.

## 9. Checklist phát hành bảo mật

- [ ] Không secret trong git history.
- [ ] `.env`, `data/`, profile trong `.gitignore`.
- [ ] TLS bật ở prod.
- [ ] Token agent ≠ token owner.
- [ ] Audit `pip-audit` & `npm audit` sạch (high/critical).
