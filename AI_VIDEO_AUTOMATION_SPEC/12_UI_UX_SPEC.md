# 12 — UI/UX SPEC

> Design system & nguyên tắc trải nghiệm cho frontend (`03`).

---

## 1. Nguyên tắc

1. **Bulk-first**: thao tác trên nhiều job dễ như trên một.
2. **Realtime rõ ràng**: luôn biết cái gì đang chạy, ở đâu, còn bao lâu.
3. **Phục hồi lỗi nhanh**: lỗi hiện kèm lý do + hành động (retry/sửa).
4. **Tối giản**: mặc định ẩn cấu hình nâng cao.

## 2. Bảng màu (Dark-first, đen + xanh dương)

| Token | Giá trị | Dùng |
|-------|---------|------|
| `--bg` | `#0B0F14` | nền chính |
| `--surface` | `#121823` | card/panel |
| `--border` | `#1E2A3A` | viền |
| `--primary` | `#2D7FF9` | hành động chính (xanh dương) |
| `--primary-hover` | `#1E6AE0` | |
| `--text` | `#E6EDF3` | chữ chính |
| `--text-muted` | `#8A97A6` | phụ |
| `--success` | `#2FB67C` | completed |
| `--warning` | `#E0A100` | retrying |
| `--danger` | `#E5484D` | failed |
| `--info` | `#3BA0FF` | running |

Light theme: đảo nền sáng, giữ accent xanh dương. Theme lưu ở `/settings`.

## 3. Typography & spacing

- Font: Inter / system-ui. Cỡ: 12/14/16/20/24/32.
- Spacing scale 4px (4,8,12,16,24,32).
- Bo góc 8px; shadow nhẹ trên surface.

## 4. Trạng thái → màu (chuẩn toàn app)

| Status | Màu | Icon |
|--------|-----|------|
| queued | muted | ⏳ |
| running | info | ▶ (pulse) |
| completed | success | ✓ |
| failed | danger | ✕ |
| retrying | warning | ↻ |
| cancelled | muted | ⊘ |

## 5. Màn hình chủ chốt (wireframe mô tả)

- **Dashboard**: hàng KPI (đang chạy / hoàn tất hôm nay / tỉ lệ lỗi / agent online) + danh sách job đang chạy + cảnh báo.
- **Batch view**: header tổng hợp (progress bar tổng), `JobGrid` filter theo status, bulk actions (retry failed, cancel).
- **Job detail**: `StepTimeline` ngang + panel log + `AssetPreview` + nút thao tác.
- **Plugins**: thẻ plugin, toggle bật/tắt, nút cấu hình mở `PluginConfigForm`.

## 6. Tương tác bulk

- Chọn nhiều job (checkbox + shift-select) → thanh hành động: Retry / Cancel / Export.
- Filter + saved view.
- Phản hồi lạc quan (optimistic) cho thao tác nhanh, rollback nếu lỗi.

## 7. Phản hồi & thông báo

- Toast cho hành động (thành công/lỗi).
- Banner kết nối WS.
- Empty-state có CTA rõ ràng.
- Skeleton khi tải.

## 8. Responsive

- Tối ưu desktop (công cụ vận hành). Tablet dùng được. Mobile chỉ xem (read-only) ở V2.0.
