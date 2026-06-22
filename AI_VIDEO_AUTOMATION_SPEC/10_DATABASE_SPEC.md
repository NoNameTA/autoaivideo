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
| id PK | trace_id | entity_type | entity_id | type | data(json) | created_at |

## 3. Index chính

- `steps(status, adapter)` — dispatcher.
- `job_queue(state, priority, enqueued_at)` — lấy việc.
- `jobs(batch_id, status)` — tổng hợp batch.
- `assets(job_id)`, `assets(checksum)`.
- `steps(idempotency_key)` unique.

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
