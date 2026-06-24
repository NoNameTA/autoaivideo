# Setup — Google Sheets Adapter (Integration Test)

> Trạng thái: **Ready for Integration Test**. Code đã implement đúng SPEC (đã duyệt), build/test xanh.
> Cần các bước dưới (owner tự làm) trước khi chạy test bằng Google Sheets THẬT. **Không commit/push
> credential. Không dán nội dung JSON vào chat.**

## 1. Tạo Google Cloud Project
1. Vào https://console.cloud.google.com/ → **Create Project** (vd `aivideo-uat`).
2. Mở **APIs & Services → Library** → bật **Google Sheets API** (và **Google Drive API** nếu mở file theo tên).

## 2. Tạo Service Account + key
1. **APIs & Services → Credentials → Create credentials → Service account**.
2. Đặt tên (vd `aivideo-sheets`) → Create → Done (không cần cấp role ở bước này).
3. Mở service account vừa tạo → tab **Keys → Add key → Create new key → JSON** → tải file về.
4. **Lấy email service account** (dạng `aivideo-sheets@<project>.iam.gserviceaccount.com`).

## 3. Share Spreadsheet cho service account
1. Tạo (hoặc dùng) 1 Google Spreadsheet thật.
2. Bấm **Share** → dán **email service account** ở bước 2.4 → quyền **Editor** → Send.
3. Lấy **Spreadsheet ID** từ URL: `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`.

## 4. Đặt file credential
- Đổi tên JSON tải về thành **`gsa.json`**, đặt vào **secrets_dir của backend** (mặc định
  `backend/.secrets`, theo `secrets_dir=./.secrets` trong `app/core/config.py`):
  ```
  C:\AIVideoPlatform\backend\.secrets\gsa.json
  ```
- Thư mục `.secrets/` đã **gitignored** (không commit). KHÔNG đưa file này lên git.
- (Tuỳ chọn prod) đặt `MASTER_KEY` (Fernet key) trong env backend → hệ thống tự dùng **Credential
  Store** mã hoá thay vì Local File, KHÔNG cần sửa adapter.

## 5. Cài dependency cho Agent
```
cd C:\AIVideoPlatform
pip install -r plugins/google_sheets/requirements.txt   # gspread (+ google-auth)
pip install cryptography                                  # nếu chạy backend chưa có
```
(Để chạy bản `.exe`: rebuild agent có bundle gspread — `cd agent && python build_exe.py`.)

## 6. Nhập trong giao diện (trang External Applications → mục "Cloud Connections")
1. **Credentials → Thêm credential:**
   - Tên: tuỳ ý (vd "Google chính").
   - Tên file bí mật **(tương đối secrets_dir)**: `gsa.json` (mặc định, sửa được). KHÔNG thêm tiền
     tố `.secrets/` — đường dẫn được giải mã tương đối `backend/.secrets`.
   - → Thêm (authentication_type = `service_account`).
2. **Connections → Thêm connection:**
   - Tên hiển thị: tuỳ ý.
   - Chọn credential vừa tạo.
   - **Spreadsheet ID**: dán ID ở bước 3.3.
   - **Worksheet Name**: tên sheet (trống = sheet đầu).
   - → Thêm.
3. Bấm **Test Connection** → kỳ vọng "Kết nối OK: <tên spreadsheet>".

## 7. Báo tôi để chạy Integration Test
Sau khi xong bước 1–6, báo tôi (chỉ cần nói "đã setup xong" + Spreadsheet ID nếu muốn tôi test ô cụ
thể). Khi đó tôi sẽ:
- Test THẬT: read / write / append / update_cell / update_row qua workflow + Test Connection.
- Browser verify · build · test · cập nhật CHANGELOG · commit · push · dừng chờ review.

> Nếu thiếu credential, hệ thống dừng ở **Ready for Integration Test** — KHÔNG mock, KHÔNG giả lập dữ liệu.
