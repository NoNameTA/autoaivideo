# 09 — COMMUNICATION PROTOCOL

> Định dạng message REST & WebSocket giữa Frontend ↔ Backend ↔ Agent.

---

## 1. Nguyên tắc chung

- JSON UTF-8. Thời gian ISO-8601 UTC. ID dạng ULID.
- Mọi WS message dùng **envelope** chung.
- Versioned: REST `/api/v1`; WS có `v` trong envelope.

## 2. WebSocket envelope

```json
{
  "v": 1,
  "type": "step.assign",
  "id": "msg_01H...",          
  "ts": "2026-06-22T10:00:00Z",
  "trace_id": "trc_01H...",
  "data": { }
}
```

- `type`: namespace.action (vd `job.updated`, `step.assign`).
- `id`: id message (để ack/dedupe).
- Server có thể yêu cầu ack: client gửi `{ "type":"ack", "data":{"id":"msg_..."} }`.

## 3. Kênh Frontend ↔ Backend (`/ws`)

Client → Server:
| type | data |
|------|------|
| `subscribe` | `{ "scope":"batch", "id":"batch_..." }` |
| `unsubscribe` | `{ "scope":"batch", "id":"batch_..." }` |

Server → Client:
| type | data |
|------|------|
| `job.updated` | `{ job_id, status, progress }` |
| `step.updated` | `{ job_id, step_id, status, progress, error? }` |
| `batch.updated` | `{ batch_id, counts:{queued,running,completed,failed} }` |
| `agent.updated` | `{ agent_id, status, capacity }` |

## 4. Kênh Backend ↔ Agent (`/ws/agent`)

Agent → Server:
| type | data |
|------|------|
| `agent.register` | `{ agent_id, version, capabilities[], capacity, os }` |
| `heartbeat` | `{ agent_id, load }` |
| `step.ack` | `{ step_id }` |
| `step.progress` | `{ step_id, pct, msg }` |
| `step.completed` | `{ step_id, assets:[{path,kind,mime,size,checksum}] }` |
| `step.failed` | `{ step_id, error, retryable: bool, screenshot? }` |

Server → Agent:
| type | data |
|------|------|
| `step.assign` | `{ step_id, job_id, capability, adapter, inputs, config, timeout }` |
| `step.cancel` | `{ step_id }` |
| `config.update` | `{ ... }` |

## 4.1 Kênh File Manager qua `/ws/agent` (SPEC 07)

FS RPC dạng request/response có `request_id` để đối soát; sự kiện watch realtime qua `fs.event`.

Server → Agent:
| type | data |
|------|------|
| `config.update` | `{ allowed_folders: string[] }` — đẩy Allowed Folders xuống agent (Permission Manager) |
| `fs.request` | `{ request_id, op, params }` — `op` ∈ `scan|read|metadata|copy|move|rename|delete|watch` |

Agent → Server:
| type | data |
|------|------|
| `fs.response` | `{ request_id, ok, result?, error?:{code,message} }` |
| `fs.event` | `{ type: created\|modified\|deleted\|moved, path, dest_path?, is_directory, ts }` (đã chuẩn hoá + debounce) |

Mã lỗi FS: `FORBIDDEN` (ngoài Allowed Folders), `NOT_FOUND`, `FS_ERROR`.

## 4.2 Dashboard Activity Stream (global, không scope)

Backend phát các bản tin **global** (mọi dashboard nhận) cho Activity Stream (SPEC 12 §5):

| type | data |
|------|------|
| `activity` | `{ kind, ... }` — `kind` ∈ `job.updated` · `plugin.runtime.{started,progress,finished,failed}` · `plugin.lifecycle.{installed,enabled,disabled,updated,removed,registration_failed}` |
| `fs.event` | (xem §4.1) — cũng hiển thị trong stream |
| `agent.updated` | trạng thái agent |

- `plugin.runtime.*` gắn với Job/Workflow (step do plugin thực thi); `plugin.lifecycle.*` thuộc quản trị registry.
- Job/step theo scope batch (§3) vẫn giữ cho BatchView; Activity Stream dùng kênh global riêng.

## 5. REST quy ước

- Phân trang: `?limit=&cursor=`; trả `{ items:[], next_cursor }`.
- Filter: `?status=running`.
- PATCH dùng partial body. POST trả 201 + resource.
- Idempotency: header `Idempotency-Key` cho POST tạo batch/job.

## 6. Định dạng lỗi (REST & WS)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Mô tả ngắn gọn cho người dùng",
    "details": [{"field":"prompt","issue":"required"}],
    "trace_id": "trc_01H..."
  }
}
```

Mã lỗi chuẩn: `VALIDATION_ERROR`, `NOT_FOUND`, `UNAUTHORIZED`, `FORBIDDEN`, `CONFLICT`, `RATE_LIMITED`, `AGENT_UNAVAILABLE`, `ADAPTER_TRANSIENT`, `ADAPTER_PERMANENT`, `INTERNAL`.

## 7. Reconnect & độ tin cậy

- Agent & Frontend tự reconnect (backoff luỹ thừa, jitter).
- Sau reconnect: agent gửi lại `agent.register` + trạng thái step đang chạy; backend đối soát.
- Message quan trọng (assign/completed) có ack; chưa ack trong timeout → gửi lại (at-least-once) → dedupe bằng `id`/`idempotency_key`.

## 8. Bảo mật kênh

- WS/REST yêu cầu token (xem `11`). Agent dùng `AGENT_TOKEN` riêng.
- Production: TLS (wss/https).
