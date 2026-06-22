# Plugin: ffmpeg

Adapter `video.ffmpeg` — chạy FFmpeg (CLI, miễn phí) để dựng/ghép/convert video (SPEC 06 cli-process).

- **inputs**: biến job (truyền qua env `STEP_INPUTS`).
- **config.args**: danh sách đối số đặt sau `ffmpeg -y -hide_banner`. Tên file output nằm trong args (ghi vào thư mục output của step).
- **config.ffmpeg_path** (tuỳ chọn): đường dẫn ffmpeg nếu không có trong PATH.

Ví dụ config tạo 1s video xanh:
```json
{ "args": ["-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1", "out.mp4"] }
```

Yêu cầu: FFmpeg cài sẵn (free). License LGPL/GPL — chỉ dùng bản phân phối hợp lệ.
