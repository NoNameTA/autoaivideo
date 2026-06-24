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

> `secret: true` phù hợp cho **bí mật đơn lẻ** nhúng trong config 1 plugin. Với **cloud API**
> (OAuth2, service-account) cần entity bí mật giàu hơn (nhiều trường, có refresh/expiry, dùng lại
> giữa nhiều adapter) → dùng **Credential Store** ở §3.1.

### 3.1 Credential Store & Credential Management (TỔNG QUÁT — dùng cho mọi cloud service)

> Mục tiêu: 1 kho bí mật **trung lập với nhà cung cấp** (Google/Notion/Dropbox/Airtable/OneDrive…),
> tách bí mật khỏi pipeline/config. Adapter chỉ tham chiếu **`credential_ref`** (id), không bao giờ
> nhúng bí mật thô.

**Credential** = bản ghi bí mật mã hoá, độc lập với plugin (schema đầy đủ ở **SPEC 10 — `credentials`**):

| Trường | Mô tả |
|---|---|
| `id` PK (`cred_…`) | định danh để tham chiếu |
| `provider` | nhãn nhà cung cấp tự do (vd `google_sheets`, `dropbox`) — **không** ràng buộc lõi |
| `connection_name` | tên người dùng đặt (vd "Google chính") |
| `authentication_type` | **V2.0: `service_account`** · roadmap: `oauth2` \| `api_key` \| `basic` \| `bearer` |
| `encrypted_secret` | **blob mã hoá** (Fernet/AES, khoá `MASTER_KEY`) chứa material thật (JSON key/token…) |
| `metadata` | json phi-bí-mật mở rộng: `scopes`, `expires_at`, `account_email`… |
| `status` | `active` \| `expired` \| `revoked` |
| `created_at` / `updated_at` / `last_used_at` | metadata thời gian |

- **Nguồn material qua Secret Provider trừu tượng (§3.5):** adapter/lõi **không** phụ thuộc nơi lưu
  cụ thể. V2.0 có 2 hiện thực: **Credential Store (DB)** mặc định + **Local Secret File** (dev/test).
- **Loại bí mật theo `authentication_type`** (V2.0 chỉ làm `service_account`):
  - `service_account`: JSON key (Google…) → ký JWT lấy access token ngắn hạn; refresh tự động.
  - *(roadmap)* `oauth2`: `client_id/secret/refresh_token` → refresh (§3.2); `api_key`/`bearer`:
    chuỗi đơn → header; `basic`: user+pass.
- **Phơi bày qua API (bắt buộc):** chỉ trả **metadata** (`id, provider, connection_name,
  authentication_type, metadata, status, created_at, updated_at, last_used_at`); **không bao giờ** trả
  `encrypted_secret`/material thật (kể cả `***`). Tạo/cập nhật: nhận material 1 chiều (write-only),
  phản hồi chỉ metadata.
- **Nhập material:** material nhạy cảm (service-account JSON) **owner tự cung cấp** (Store hoặc Local
  File); hệ thống không tự tạo tài khoản, không tự sinh OAuth, **không** commit/log/push credential.

### 3.2 OAuth2 / token refresh

- Access token ngắn hạn được **cache trong `encrypted_secret`** (tại Backend) kèm `expiry`; khi
  `now ≥ expiry − skew` → Backend dùng `refresh_token` (oauth2) hoặc JWT-sign (service_account) lấy
  token mới, ghi đè cache.
- **Refresh chạy ở Backend** (nơi duy nhất giữ secret — D1, §3.3), **không** ở Agent. Agent chỉ nhận
  access token ngắn hạn đúng-lúc-đúng-op.
- `refresh_token` xoay vòng (rotation) nếu provider trả token mới → Backend lưu lại ngay.
- `401/403` từ API (Agent gặp) → báo Backend thử refresh 1 lần & cấp token mới; vẫn lỗi →
  `PermanentError` "cần cấp lại quyền".

### 3.3 Đường đi credential — Backend là nơi DUY NHẤT giữ Secret (D1 đã duyệt)

**Nguyên tắc:** Agent KHÔNG bao giờ là nơi lưu secret; Backend quản lý toàn bộ.

1. **Backend giữ khoá & kho:** chỉ Backend có `MASTER_KEY`; `encrypted_secret` chỉ giải mã **tại
   Backend**. Agent **không** giữ `MASTER_KEY`, **không** giữ `encrypted_secret`.
2. **Giải mã just-in-time:** Backend chỉ giải mã **khi Agent thực sự cần thực hiện một operation**
   (không giải mã sẵn lúc assign job/step).
3. **Gửi tối thiểu, theo từng operation:** khi tới op `cloud-api`, Agent gửi yêu cầu credential qua
   **kênh bảo mật `/ws/agent` (wss)** (RPC correlation-id, theo mẫu `fs_rpc` SPEC 09 §4.1 — **cần
   bổ sung 1 message `credential.request/response` ở SPEC 09; ngoài phạm vi 06/08/10/11 → điểm duyệt**).
   Backend trả **lượng tối thiểu** cần cho op đó — **ưu tiên material dẫn xuất ngắn hạn** (vd
   **access token** đã ký từ service-account) thay vì JSON key gốc, kèm `expiry` ngắn.
4. **Agent RAM-only + xoá sau op:** material chỉ tồn tại trong RAM Agent **trong lúc thực thi op**;
   hoàn thành (hoặc lỗi) → **xoá khỏi bộ nhớ ngay**. Agent **tuyệt đối không** ghi credential ra
   **log / file / cache lâu dài / DB cục bộ**, không gửi lên Frontend.
5. **Refresh:** việc refresh token (service_account JWT-sign; oauth2 ở roadmap) thực hiện **tại
   Backend** rồi cấp token ngắn hạn xuống Agent (Agent không tự refresh, không giữ refresh_token).
6. **Redaction:** material + token **không** vào log/console/screenshot (mở rộng §6); audit-log chỉ
   ghi `credential_ref`/`connection_id` + `provider`, **không** ghi nội dung bí mật.

> So với draft trước (Backend đẩy material trong `step.assign`): mô hình này **chặt hơn** — không
> đính kèm secret vào envelope assign, chỉ cấp đúng-lúc/đúng-op và token ngắn hạn → giảm bề mặt rò rỉ.

### 3.4 Connection Manager (kết nối có cấu hình) — quản lý ở trang External Apps

- **Connection** = (adapter/`capabilities`) + `credential_id` + `settings` phi-bí-mật (vd
  `spreadsheet_id` mặc định). Schema ở **SPEC 10 — `connections`**. Tạo & **Test kết nối** ở trang
  External Apps (SPEC 06 §10).
- **Connection Manager dùng chung** (mọi Cloud Adapter): quản lý **nhiều kết nối cùng lúc** — vd
  *Google Sheets A*, *Google Sheets B*, *Google Drive*, *Dropbox*, *OneDrive*… — không kiến trúc
  riêng cho từng dịch vụ.
- Connection **không** chứa bí mật (chỉ trỏ `credential_id`) → an toàn để hiển thị/sửa. 1 credential
  có thể dùng cho nhiều connection. Trường: `display_name`, `health_status`, `last_check`,
  `capabilities`, `settings` (phi-bí-mật) — schema **SPEC 10 — `connections`**.

### 3.5 Secret Provider — backend lưu bí mật **có thể thay thế** (pluggable, AP4)

> Lõi đọc/ghi bí mật qua **1 interface trừu tượng `SecretProvider`** → đổi backend lưu trữ
> **không cần sửa Adapter**.

- **Interface** (khái niệm): `get(ref) / put(material) / rotate(ref) / delete(ref) / list_meta()`.
  Adapter & Credential Service chỉ gọi interface, không biết backend cụ thể.
- **Hiện thực V2.0:**
  - `db_store` (**mặc định, prod ưu tiên**): bảng `credentials`, `encrypted_secret` mã hoá Fernet
    (`MASTER_KEY`). Không có `MASTER_KEY` ở prod → từ chối khởi tạo (fail-safe).
  - `local_file` (**chỉ Development / Testing / Single-machine**): file bí mật **gitignored** (vd
    service-account JSON) trỏ qua đường dẫn config/env; validate path (§5), ngoài repo.
- **Roadmap (không sửa Adapter):** `windows_credential_manager`, `hashicorp_vault`, `azure_key_vault`,
  `aws_secrets_manager`, … — chỉ thêm hiện thực `SecretProvider`, cấu hình chọn backend.
- **Production:** ưu tiên `db_store` (hoặc external vault); hạn chế `local_file`.

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
