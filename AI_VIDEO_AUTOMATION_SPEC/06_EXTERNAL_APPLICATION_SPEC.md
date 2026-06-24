# 06 — EXTERNAL APPLICATION SPEC

> Chuẩn tích hợp một "ứng dụng/dịch vụ ngoài" (External App) mà Agent điều khiển. Mỗi External App được bọc bởi một Adapter (xem `08`).

---

## 1. Định nghĩa

**External Application** = bất kỳ công cụ ngoài lõi nền tảng được dùng để thực hiện một Step:
- Web app (trình tạo ảnh/video AI miễn phí, TTS online) → điều khiển qua **CDP**.
- Desktop app (trình dựng video, ffmpeg GUI) → điều khiển qua **UI automation** hoặc CLI.
- CLI/local tool (ffmpeg, whisper.cpp) → gọi trực tiếp process.
- **Dịch vụ cloud có API** (Google Sheets/Drive/Docs/Calendar, Notion, Dropbox, OneDrive, Airtable…)
  → gọi **REST/API** qua adapter loại `cloud-api` (xem §9). Đây là khung **tổng quát**, không thiết
  kế riêng cho nhà cung cấp nào.

⚠️ Mọi External App phải **miễn phí** và tuân thủ `14_FREE_SOFTWARE_POLICY.md`, đồng thời tôn trọng ToS của dịch vụ.

## 2. Phân loại tích hợp

| Loại | Cơ chế | Ví dụ |
|------|--------|------|
| `web-cdp` | Playwright/CDP điều khiển trình duyệt | trình sinh ảnh AI web miễn phí |
| `desktop-uia` | UI automation cửa sổ native | app dựng video desktop |
| `cli-process` | Spawn process + args | ffmpeg, whisper.cpp, yt-dlp |
| `local-http` | App ngoài expose HTTP localhost | server TTS/LLM chạy máy (vd local model) |
| `cloud-api` | **REST/API cloud qua HTTP + xác thực** (api-key/oauth2/service-account) | Google Sheets/Drive/Docs/Calendar, Notion, Dropbox, OneDrive, Airtable |

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

---

## 9. Cloud API Integration (`cloud-api`) — KHUNG TỔNG QUÁT

> Khung dùng chung cho **mọi dịch vụ cloud có API** (Google Sheets/Drive/Docs/Calendar, Notion,
> Dropbox, OneDrive, Airtable, OpenAI, Anthropic…). Google Sheets là **adapter đầu tiên dùng khung
> này** (§11), KHÔNG phải thiết kế riêng cho Google. Mọi logic đặc thù nằm trong plugin; lõi chỉ biết
> `capability` + khung chung (theo §7 + SPEC 08). Tất cả Cloud Adapter dùng chung: **Credential Store**
> (SPEC 11 §3.1) · **Connection Manager** (§10, SPEC 11 §3.4) · **driver `cloud`** (§9.1) · quy ước
> capability `cloud.<service>.<operation>` (§9.6).
>
> ⚠️ **Free-policy (SPEC 14):** khung trung lập nhà cung cấp, nhưng **mỗi adapter vẫn chịu cổng
> `free` của SPEC 14**. Dịch vụ có free-tier hợp lệ (vd Google Sheets API trong quota) → `free: true`.
> Dịch vụ **trả phí** (vd OpenAI/Anthropic) → thuộc diện **SPEC 14 §6** (plugin tuỳ chọn, `free: false`,
> CI chặn mặc định, cần override có lý do). **Việc bật adapter trả phí cần owner quyết** (điểm duyệt).

### 9.1 Driver `cloud` (mới — cạnh `cdp`/`uia`/`process`)
Agent cung cấp driver `cloud` lo phần **hạ tầng chung**, plugin chỉ gọi nghiệp vụ:
| Hàm | Mô tả |
|---|---|
| `request(method, path, *, params, json, headers)` | HTTP có `base_url`, **tự gắn xác thực**, retry/backoff |
| `paginate(path, *, cursor_field, items_field)` | trợ giúp phân trang (page token/offset) |
| `auth()` | xin **token ngắn hạn** từ Backend đúng-lúc-đúng-op (§9.2, SPEC 11 §3.3); **không** tự giữ/refresh secret |
| `rate_limit_guard()` | tôn trọng `429`/`Retry-After` → `TransientError` |

- Driver dùng HTTP client chung (`httpx`, đã có ở Agent). **Không** ràng buộc SDK riêng của nhà cung cấp ở lõi.
- SDK nhà cung cấp (vd `gspread`/`google-api-python-client`) — nếu plugin chọn dùng — **đóng gói
  trong plugin đó**, không thêm vào lõi (xem §11 Dependencies).

### 9.2 Xác thực & credential
- Adapter `cloud-api` **không nhúng bí mật**; manifest khai báo **yêu cầu credential** (`auth`),
  step/connection truyền **`credential_ref`/`connection_id`** → driver lấy material qua **Credential
  Store (SPEC 11 §3.1)**, nguồn từ DB Store **hoặc** Local Secret File (SPEC 11 §3.1).
- `auth.kind`: **V2.0 chỉ `service_account`**; roadmap `oauth2 | api_key | basic | bearer`.
  `auth.scopes` liệt kê phạm vi cần.
- **Đường đi bí mật (SPEC 11 §3.3 — D1):** Backend giữ & giải mã, cấp **token ngắn hạn đúng-lúc-đúng-op**
  cho Agent qua wss; Agent giữ trong RAM lúc chạy op rồi **xoá ngay**, không log/file/cache. Refresh
  token ở **Backend** (SPEC 11 §3.2).

### 9.3 Healthcheck
- `healthcheck` = 1 lệnh API nhẹ (vd GET metadata) xác nhận **auth hợp lệ + dịch vụ tới được**.
  Dùng cho nút **Test kết nối** (§10) và `prepare`.

### 9.4 Ánh xạ vòng đời (SPEC 08 §4)
| Lifecycle | cloud-api |
|---|---|
| `validate_config` | kiểm tra selector tài nguyên (id spreadsheet/range…) + có `credential_ref`/`connection_id` |
| `prepare` | `auth()` (xin token ngắn hạn từ Backend §9.2) + `healthcheck` |
| `run` | gọi API nghiệp vụ (đọc/ghi…) qua `ctx.driver.request`; `ctx.progress` cho thao tác dài |
| `collect` | ghi kết quả ra Asset (SPEC 07) nếu có (vd export CSV/JSON đọc được) |
| `cleanup` | đóng client/huỷ token tạm |

### 9.5 Ánh xạ lỗi (chuẩn hoá cho mọi cloud)
| Tình huống | HTTP | Xử lý |
|---|---|---|
| Rate limit | 429 (+`Retry-After`) | `TransientError` (backoff) |
| Mạng/timeout/5xx | 5xx, lỗi mạng | `TransientError` (retry) |
| Hết hạn/sai quyền | 401/403 | báo Backend refresh & cấp token mới 1 lần → vẫn lỗi: `PermanentError` "cần cấp lại quyền" |
| Tài nguyên không tồn tại/selector sai | 404/400 | `PermanentError` |
| Xung đột ghi | 409 | `PermanentError` (hoặc retry có điều kiện) |

### 9.6 Mô hình Tài nguyên Cloud (TỔNG QUÁT — để tái sử dụng)
Hầu hết dịch vụ map về cây **Account → Container → (Sub-container) → Item/Records**:

| Generic | Sheets | Drive | Docs | Calendar | Notion | Dropbox/OneDrive | Airtable |
|---|---|---|---|---|---|---|---|
| Container | Spreadsheet | Folder | Document | Calendar | Database | Folder | Base |
| Sub-container | Worksheet | — | — | — | — | — | Table |
| Item | Row/Cell | File | Block | Event | Page/Row | File | Record |

**Bộ thao tác chuẩn** (mỗi op = 1 `capability`, đặt tên `cloud.<service>.<op>` — đồng bộ kiểu
`video.ffmpeg`, `web.cdp`):
`list_containers` · `list_subcontainers` · `read` · `write`/`append` · `update_cell`(/field) ·
`update_row`(/record) · `changes` (poll-watch §9.7). Adapter chỉ hiện thực các op nó hỗ trợ.

### 9.7 Theo dõi thay đổi (change-tracking) — **D4 đã duyệt**
> Watch hiện tại (SPEC 07 §8) chỉ cho **file cục bộ** (watchdog). Cloud không có watchdog.
- **V2.0 (phạm vi hiện tại):** chỉ thao tác **Read / Write / Update** chạy theo **Manual Run /
  Workflow Run / Cron**. **KHÔNG** triển khai Poller nền. Adapter **có thể** hiện thực op tuỳ chọn
  `cloud.<service>.changes(cursor)` → `{items, next_cursor}` để gọi **thủ công/cron**, nhưng không có
  thành phần lập lịch nền ở V2.0.
- **V2.1 (roadmap):** **Poller nền** (mới) chạy theo `interval`, gọi `changes(cursor)`, phát `activity`
  (SPEC 09 §4.2) → realtime UI. Không mở rộng ở V2.0.

### 9.8 Provider Framework (metadata nhà cung cấp — AP2, TỔNG QUÁT)
> Mỗi nhà cung cấp khai báo **metadata** chuẩn; lõi & CI xử lý **theo policy**, **không hard-code**
> theo từng provider. Cổng `free` (SPEC 14) đọc metadata này.

**Trường metadata provider (bắt buộc):**
`provider` · `category` · `auth_type` · `free` · `commercial` · `requires_api_key` · `requires_oauth`.

| provider | category | auth_type | free | commercial | requires_api_key | requires_oauth |
|---|---|---|---|---|---|---|
| `google_sheets` | productivity | service_account | ✅ | ❌ | ❌ | ❌ |
| `google_drive` | storage | service_account | ✅ | ❌ | ❌ | ❌ |
| `google_docs` | productivity | service_account | ✅ | ❌ | ❌ | ❌ |
| `google_calendar` | calendar | service_account | ✅ | ❌ | ❌ | ❌ |
| `notion` | productivity | api_key/oauth2 | ✅ | ❌ | ✅ | (oauth roadmap) |
| `dropbox` | storage | oauth2 | ✅ | ❌ | ❌ | ✅ |
| `onedrive` | storage | oauth2 | ✅ | ❌ | ❌ | ✅ |
| `airtable` | database | api_key | ✅ | ❌ | ✅ | ❌ |
| `openai` | ai | api_key | ❌ | ✅ | ✅ | ❌ |
| `anthropic` | ai | api_key | ❌ | ✅ | ✅ | ❌ |
| `claude_desktop` | ai-desktop | — | ❌ | ✅ | ❌ | ❌ |

- **Framework hỗ trợ cả 2 nhóm** (free & commercial). Việc **bật** provider `free:false` chịu cổng
  SPEC 14 §6 (policy-driven, CI cảnh báo/chặn theo policy — không hard-code per provider).
- **V2.0 chỉ hiện thực `auth_type = service_account`** (D5); `api_key`/`oauth2` ở roadmap. Metadata vẫn
  khai đầy đủ để chuẩn bị.

---

## 10. Quản lý kết nối (Connection) — trang External Apps

- **Connection** (SPEC 11 §3.4) = adapter + `credential_ref` + cấu hình phi-bí-mật. Người dùng quản
  lý ở **trang External Apps**: tạo/sửa/xoá Connection, chọn Credential, **Test kết nối** (chạy
  `healthcheck` thật §9.3), bật/tắt.
- Trang External Apps mở rộng: ngoài liệt kê adapter (đã có), thêm khu **Connections** cho nhóm
  `cloud-api` (và bất kỳ adapter cần credential). Connection KHÔNG hiển thị bí mật.

---

## 11. Adapter đầu tiên dùng khung: Google Sheets (hợp đồng cụ thể)

> Là **ví dụ tham chiếu** cho `cloud-api`, không phải thiết kế riêng. Cài như plugin
> `plugins/google_sheets/` (SPEC 08), không sửa lõi.

### 11.1 Capabilities (theo §9.6 — `cloud.<service>.<operation>`, D6)
`cloud.google_sheets.read` · `cloud.google_sheets.write` · `cloud.google_sheets.append` ·
`cloud.google_sheets.update_cell` · `cloud.google_sheets.update_row` ·
(tuỳ chọn, gọi thủ công/cron — §9.7) `cloud.google_sheets.changes`.

### 11.2 Manifest (mở rộng SPEC 08 §3 cho cloud-api; trường free-policy theo SPEC 14 §3)
```yaml
name: google_sheets
type: cloud-api
free: true                                   # Google Sheets API có free-tier trong quota (SPEC 14)
license: Apache-2.0                           # thư viện gspread/google-auth (Apache-2.0)
source_url: https://developers.google.com/sheets
tos_url: https://developers.google.com/terms
automation_allowed: true                      # dùng API chính thức trong quota (D7)
base_url: https://sheets.googleapis.com/v4
auth:
  kind: service_account                       # V2.0 chỉ service_account (D5); oauth2 = roadmap
  scopes: [ "https://www.googleapis.com/auth/spreadsheets" ]
requires_credential: true                     # phải có credential_ref/connection_id khi chạy
capabilities:
  - cloud.google_sheets.read
  - cloud.google_sheets.write
  - cloud.google_sheets.append
  - cloud.google_sheets.update_cell
  - cloud.google_sheets.update_row
config_schema: config.schema.json
```

### 11.3 Config (chọn tài nguyên — non-secret)
`spreadsheet_id` (chọn Spreadsheet) · `worksheet` (tên/`gid`) · `range` (A1, vd `A1:D10`) ·
`value_input_option` (RAW/USER_ENTERED) · với `update_cell`: `cell`+`value`; với `update_row`:
`row_index`+`values`. **Bí mật KHÔNG ở đây** — qua `credential_ref`/`connection_id`.

### 11.4 Dependencies (D3 đã duyệt)
- **Plugin** `plugins/google_sheets/`: **`gspread`** (Apache-2.0, free) — khai trong requirements của
  plugin/agent extra, **không** ở lõi backend. Nếu cần Google API nâng cao sau này → mở rộng sang
  `google-api-python-client` + `google-auth` (cùng họ Apache-2.0).
- **Lõi/Agent** (chung cloud-api): `httpx` (đã có). **Credential Store (lõi):** **`cryptography`**
  (Fernet) — thêm mới cho SPEC 11 §3.1 (đã duyệt D3).
- **Không** thêm dependency ngoài phạm vi trên nếu chưa được duyệt.

### 11.5 Test thật (không mock — D8)
- Owner tự tạo & cung cấp: **Google Cloud Project + Service Account JSON** + **Spreadsheet thật** đã
  share quyền cho service account. Hệ thống **không** tự tạo tài khoản/không tự cấp quyền.
- Adapter nạp credential từ **Credential Store** *hoặc* **Local Secret File** (SPEC 11 §3.1). Credential
  **không** commit/push/log/ghi CHANGELOG.
- Kịch bản: tạo Credential → tạo Connection → **Test kết nối** (healthcheck §9.3) → Read range →
  Write/Append → Update cell → Update row → *(tuỳ chọn)* changes (thủ công).
