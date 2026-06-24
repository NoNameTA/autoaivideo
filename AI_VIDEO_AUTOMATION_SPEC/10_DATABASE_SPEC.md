# 10 — DATABASE SPEC

> SQLite mặc định (file `data/app.db`), Postgres tuỳ chọn. ORM: SQLAlchemy async. Migration: Alembic.

---

## 1. Sơ đồ quan hệ (ERD tóm tắt)

```
projects 1───* batches 1───* jobs 1───* steps 1───* assets
                                   │
agents 1───* steps (assigned_agent)│
plugins (registry)                 │
job_queue ───► steps               │
events (audit/log) ────────────────┘
credentials 1───* connections      (Cloud Adapter — SPEC 06 §9, 11 §3)
```

## 2. Bảng

### projects
| cột | kiểu | ghi chú |
|-----|------|--------|
| id | ULID PK | |
| name | text | |
| description | text | |
| default_pipeline | text | tên template |
| config | json | mặc định cho batch |
| created_at / updated_at | timestamptz | |

### batches
| id PK | project_id FK | name | status | input_count | counts(json) | created_at |

`status`: `created|running|completed|failed|cancelled`. `counts` cache số job theo trạng thái.

### jobs
| id PK | batch_id FK | seq(int) | status | pipeline | vars(json) | progress(int) | error(text) | created_at | updated_at |

`status`: `queued|running|completed|failed|cancelled`.

### steps
| cột | kiểu |
|-----|------|
| id PK | ULID |
| job_id FK | |
| step_key | text (vd `voice`) |
| order | int |
| adapter | text (capability) |
| status | `queued|assigned|running|completed|failed|retrying|cancelled` |
| attempt | int |
| max_retries | int |
| assigned_agent | FK agents nullable |
| inputs / config | json |
| error | text |
| started_at / finished_at | timestamptz |
| idempotency_key | text unique |

### assets
| id PK | step_id FK | job_id FK | kind | path(rel) | mime | size | checksum(sha256) | created_at |

`kind`: `script|audio|image|subtitle|video|export|screenshot|other`.

### agents
| id PK (agent_id) | version | capabilities(json) | capacity | status(`online|offline|busy`) | os | last_heartbeat | registered_at |

### plugins
| name PK | version | capability | type | enabled(bool) | config(json) | manifest(json) | installed_at |

### job_queue (durable queue)
| id PK | step_id FK | priority(int) | state(`pending|leased|done`) | lease_until | enqueued_at |

### events (audit/log)
| id PK | trace_id | entity_type | entity_id | type | level | data(json) | created_at |

`level` ∈ `info|warn|error|debug` — suy ra từ loại event lúc ghi (04 §7). Index `level` để lọc
trang Logs. `data` chứa context denormalize (`batch_id`/`project_id`/`capability`…) cho lọc/tìm kiếm.

### credentials (Credential Store — SPEC 11 §3.1)
> **Tổng quát, KHÔNG hard-code cho Google.** Dùng chung cho mọi Cloud Adapter
> (Google Sheets/Drive/Docs/Calendar, Dropbox, OneDrive, Notion, Airtable, OpenAI, Anthropic…).

| cột | kiểu | ghi chú |
|-----|------|--------|
| id PK (`cred_…`) | ULID | |
| provider | text | nhãn nhà cung cấp tự do (vd `google_sheets`, `dropbox`) — **không** ràng buộc lõi |
| connection_name | text | tên người dùng đặt (vd "Google chính") |
| authentication_type | text | `service_account` (V2.0) \| `oauth2` \| `api_key` \| `basic` \| `bearer` |
| encrypted_secret | blob/text | **bí mật mã hoá** (Fernet/AES, khoá `MASTER_KEY`) — **không** plaintext; API **không** trả |
| metadata | json | mở rộng linh hoạt: `scopes`, `expires_at`, `account_email`, … (không bí mật) |
| status | text | `active` \| `expired` \| `revoked` |
| created_at / updated_at / last_used_at | timestamptz | |

### connections (Connection Manager — SPEC 06 §10, 11 §3.4)
> Quản lý **nhiều kết nối cùng lúc** (Google Sheets A/B, Drive, Dropbox…). Connection **không** chứa
> bí mật — chỉ trỏ `credential_id` + cấu hình phi-bí-mật.

| cột | kiểu | ghi chú |
|-----|------|--------|
| id PK (`conn_…`) | ULID | |
| provider | text | khớp/độc lập với credential.provider |
| credential_id | FK credentials nullable | bí mật dùng cho kết nối |
| display_name | text | tên kết nối (vd "Sheet doanh thu") |
| enabled | bool | bật/tắt |
| health_status | text | `connected` \| `error` \| `disabled` \| `unknown` (cập nhật khi Test kết nối) |
| last_check | timestamptz | lần test kết nối gần nhất |
| capabilities | json | nhóm capability dùng (vd `["cloud.google_sheets.read", …]` hoặc prefix) |
| settings | json | **phi-bí-mật** (vd `spreadsheet_id`, `worksheet`, `base_folder`) |
| created_at / updated_at / last_used_at | timestamptz | |

- Step `cloud-api` tham chiếu bí mật qua `credential_ref` (= `credential_id`) trong `steps.config`,
  có thể gián tiếp qua `connection_id`. **Không** lưu bí mật trong `steps`/`pipelines`.

### video_sources (Video Sources — lớp nguồn dữ liệu đầu vào)
> Quản lý **nguồn video đầu vào** (link/Sheet/CSV/Folder…). `source_type` mở rộng để thêm nguồn mới
> mà **không sửa Workflow/Queue** (SPEC 02). Website chỉ quản lý danh sách + tạo Job; **Agent** mới tải.

| cột | kiểu | ghi chú |
|-----|------|--------|
| id PK (`vsrc_…`) | ULID | |
| name | text | tên nguồn |
| source_type | text | `direct_url` (V1) \| `google_sheets` \| `csv` \| `folder` \| … (mở rộng) |
| config | json | cấu hình theo loại (vd Sheets: connection_id/url_column) — **không** bí mật |
| status | text | `draft` \| `imported` \| `running` \| `done` |
| item_count | int | số video (cache) |
| created_at / updated_at | timestamptz | |

### video_source_items (mỗi link video)
| cột | kiểu | ghi chú |
|-----|------|--------|
| id PK (`vitem_…`) | ULID | |
| source_id FK | → video_sources (cascade) | |
| seq | int | thứ tự (STT) |
| url | text | link video |
| title | text nullable | tên video (nếu có) |
| status | text | `pending` \| `processing` \| `done` \| `failed` (suy từ job đã link khi đọc) |
| job_id | FK jobs nullable | job tạo khi Run Workflow |
| created_at / updated_at | timestamptz | |

- **Run Workflow** → tạo Batch (Project→Batch→Job hiện có) với mỗi item = 1 input row → 1 Job;
  pipeline download (vd `video_download`, step `media.download`/yt-dlp). **KHÔNG** sửa engine/queue;
  trạng thái item suy từ `jobs.status` khi đọc.

## 3. Index chính

- `steps(status, adapter)` — dispatcher.
- `job_queue(state, priority, enqueued_at)` — lấy việc.
- `jobs(batch_id, status)` — tổng hợp batch.
- `assets(job_id)`, `assets(checksum)`.
- `steps(idempotency_key)` unique.
- `credentials(provider, status)`, `connections(provider, enabled)` — liệt kê theo nhà cung cấp.

## 4. Toàn vẹn & giao dịch

- Tạo batch → insert batch + jobs + steps + job_queue trong **một transaction**.
- Cập nhật step status + enqueue next step transaction-safe.
- Xoá job → xoá steps/assets/queue + file system (file xoá sau khi DB commit).

## 5. Migration

- Alembic; mỗi thay đổi schema = 1 revision có up/down.
- Startup kiểm tra `alembic heads` khớp; lệch → cảnh báo/không khởi động ở prod.
- SQLite: bật `PRAGMA foreign_keys=ON`, `journal_mode=WAL`.

## 6. Khác biệt SQLite vs Postgres

| Vấn đề | SQLite | Postgres |
|--------|--------|---------|
| json | `JSON` text | `JSONB` |
| đồng thời ghi | giới hạn (WAL) | cao |
| khuyến nghị | dev / 1 máy | nhiều agent / tải cao |

`DATABASE_URL` quyết định driver. Mã dùng SQLAlchemy nên portable; tránh SQL phương ngữ đặc thù.

## 7. Sao lưu

- SQLite: copy file `app.db` khi WAL checkpoint (job backup định kỳ → `data/backups/`).
- Postgres: `pg_dump` theo lịch.
