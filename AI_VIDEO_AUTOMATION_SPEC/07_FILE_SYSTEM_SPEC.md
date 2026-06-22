# 07 — FILE SYSTEM SPEC

> Cấu trúc thư mục runtime cho asset & artefact. Trạng thái thật ở DB (`10`); file system chỉ lưu asset.

---

## 1. Gốc dữ liệu

`DATA_DIR` (mặc định `C:\AIVideoPlatform\data`).

```
data/
├── projects/
│   └── {project_id}/
│       ├── project.json                 # snapshot cấu hình (đọc-thêm)
│       └── batches/
│           └── {batch_id}/
│               ├── input.csv            # input gốc
│               └── jobs/
│                   └── {job_id}/
│                       ├── job.json      # metadata job
│                       ├── steps/
│                       │   └── {step_id}/
│                       │       ├── inputs/
│                       │       ├── outputs/        # asset sinh ra
│                       │       └── step.log
│                       └── final/        # video cuối + export
├── plugins/                # asset/cache riêng của plugin
├── tmp/                    # tạm, dọn định kỳ
└── logs/                   # log hệ thống
```

## 2. Quy tắc đặt tên

- ID dạng ULID/UUID (sortable). Thư mục theo ID, không theo tên người dùng (tránh ký tự lạ).
- Asset: `{step_id}__{kind}__{index}.{ext}` — vd `01H..__image__001.png`, `voice.mp3`, `final.mp4`.
- Không dấu cách, không ký tự đặc biệt; lowercase ext.

## 3. Quy ước Asset

Mỗi asset ghi 1 dòng trong DB bảng `assets` gồm `path` (tương đối DATA_DIR), `kind`, `mime`, `size`, `checksum (sha256)`. File system + DB phải khớp; có job dọn rác (orphan) định kỳ.

## 4. Vòng đời file

| Giai đoạn | Hành động |
|----------|----------|
| Tạo job | tạo cây thư mục job |
| Chạy step | ghi vào `steps/{id}/outputs/` |
| Hoàn tất job | gom kết quả vào `final/` |
| Export | copy/hardlink sang `final/export/` |
| Xoá job | xoá cây thư mục + dòng DB (transaction-safe) |
| Dọn tmp | xoá `tmp/` cũ hơn N giờ |

## 5. Đồng bộ giữa Agent và Backend

- Agent ghi asset cục bộ trên máy agent theo cùng cấu trúc, rồi:
  - **Cùng máy**: backend đọc trực tiếp.
  - **Khác máy**: agent upload asset qua endpoint `POST /jobs/{id}/steps/{sid}/assets` (multipart) → backend lưu vào DATA_DIR.
- Checksum kiểm tra toàn vẹn khi nhận.

## 6. Dung lượng & dọn dẹp

- Cấu hình `retention_days` cho asset trung gian (giữ `final/`).
- Cảnh báo khi đĩa < ngưỡng (mặc định 5GB) → tạm dừng nhận job mới.

## 7. Quyền & an toàn

- `DATA_DIR` không nằm trong repo Git (thêm vào `.gitignore`).
- Không lưu secret trong file asset/metadata.
- Đường dẫn luôn validate để chống path traversal (xem `11`).
