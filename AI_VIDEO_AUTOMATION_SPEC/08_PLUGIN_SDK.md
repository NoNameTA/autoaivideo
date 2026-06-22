# 08 — PLUGIN SDK

> Cách viết plugin/adapter để thêm External App mới mà không sửa lõi. Tham chiếu `06`, `05`, `09`.

---

## 1. Triết lý

Lõi chỉ biết **capability** (vd `image.free_gen`), không biết app cụ thể. Một **Plugin** cung cấp một hoặc nhiều **Adapter**, mỗi adapter hiện thực một capability. Plugin nạp qua entry-points / thư mục `plugins/`.

## 2. Cấu trúc plugin

```
plugins/free_image_gen/
├── manifest.yaml          # metadata (xem 06 §3)
├── adapter.py             # class Adapter
├── config.schema.json     # JSON Schema cho cấu hình
└── README.md
```

## 3. Manifest

```yaml
name: free_image_gen
version: 1.0.0
capability: image.free_gen
type: web-cdp                 # web-cdp | desktop-uia | cli-process | local-http
free: true                    # BẮT BUỘC true (xem 14)
license: MIT
source_url: https://...
entrypoint: adapter:FreeImageGenAdapter
config_schema: config.schema.json
```

## 4. Base Adapter (interface)

```python
from sdk import Adapter, StepContext, Asset, TransientError, PermanentError

class FreeImageGenAdapter(Adapter):
    capability = "image.free_gen"

    def validate_config(self, config: dict) -> None:
        """Raise nếu config sai (đã được check sơ bộ bằng JSON Schema)."""

    async def prepare(self, ctx: StepContext) -> None:
        """Mở app/đăng nhập/healthcheck. Dùng ctx.driver (cdp/uia/process)."""

    async def run(self, ctx: StepContext) -> None:
        """Thực hiện công việc. Gọi ctx.progress(pct, msg) để báo tiến độ."""
        ...
        if rate_limited: raise TransientError("rate limit")
        if selector_missing: raise PermanentError("UI changed")

    async def collect(self, ctx: StepContext) -> list[Asset]:
        """Tải file kết quả, trả danh sách Asset (đường dẫn theo 07)."""

    async def cleanup(self, ctx: StepContext) -> None:
        """Đóng tab/process, dọn tạm."""
```

### StepContext cung cấp
- `ctx.inputs: dict` — input đã resolve (file/biến).
- `ctx.config: dict` — cấu hình plugin (đã validate).
- `ctx.driver` — driver phù hợp type (`cdp` | `uia` | `process`).
- `ctx.fs` — API ghi asset đúng chuẩn `07`.
- `ctx.progress(pct, msg)` — báo tiến độ (→ `step.progress`).
- `ctx.logger`, `ctx.trace_id`.

## 5. Driver API (tóm tắt)

| Driver | Hàm chính |
|--------|----------|
| `cdp` | `goto, click, type, fill, wait_for, eval, download, screenshot` |
| `uia` | `focus_window, click_control, type_keys, get_text, wait_control` |
| `process` | `run(cmd, args, timeout) -> {code, stdout, stderr}` |

## 6. Phân loại lỗi (bắt buộc)

- `TransientError` → engine retry (rate limit, mạng, app bận).
- `PermanentError` → fail ngay (UI đổi, captcha, input sai). Kèm screenshot/log.

## 7. Cấu hình động trên Frontend

Frontend đọc `GET /plugins/{name}/schema` (chính là `config.schema.json`) và sinh form tự động (`PluginConfigForm`, `03`). Vì vậy schema phải đủ mô tả (`title`, `description`, `default`, `format`, `secret: true` cho field nhạy cảm).

## 8. Đăng ký & nạp

- Backend `PluginService` quét `plugins/` + entry-points → `registry`.
- Agent nạp adapter tương ứng capability nó khai báo.
- Bật/tắt plugin ở `/plugins` (frontend) → lưu DB.

## 9. Kiểm thử plugin

- Mỗi plugin kèm test contract: validate_config, mock driver cho run/collect.
- CI chạy "plugin contract test" (xem `15`).

## 10. Quy tắc tương thích

- SemVer cho plugin. Lõi khai báo `sdk_version`; plugin khai `requires_sdk`.
- Không phá vỡ interface Adapter trong cùng major.
