# Plugins

Thư mục chứa plugin/adapter cho **External Applications** (SPEC `08_PLUGIN_SDK.md`, `06_EXTERNAL_APPLICATION_SPEC.md`).

## Cấu trúc mỗi plugin (theo SPEC 08 §2)

```
plugins/<name>/
├── manifest.yaml        # metadata (capability, type, free, license...)
├── adapter.py           # class Adapter (prepare/run/collect/cleanup)
├── config.schema.json   # JSON Schema cho cấu hình (frontend sinh form)
└── README.md
```

> Theo quyết định dự án: giữ định dạng SPEC (`manifest.yaml` + `config.schema.json`).

## Plugin dự kiến (Phase 5 — Plugin System)

Chỉ build + kiểm thử thật các adapter cho app đang có/cài được:

| Plugin | Cơ chế (SPEC 06 §2) | Trạng thái |
|--------|---------------------|-----------|
| `ffmpeg` | cli-process | ✅ làm được (cần ffmpeg) |
| `yt_dlp` | cli-process | ✅ làm được (pip) |
| `chrome` / `edge` | web-cdp (Playwright) | ✅ khi cài Playwright |
| `google_sheets` | local-http/cli (public sheet) | ✅ |
| `explorer` | cli-process / OS API | ✅ |
| `bulk_video_studio` | web-cdp (CDP window.api) | ⏸ HOÃN — app đã gỡ khỏi máy |
| `obs` | local-http (obs-websocket) | ⏸ HOÃN — chưa cài OBS |

Không sửa mã nguồn chính khi thêm plugin (SPEC 08 §1, 18 §1).
