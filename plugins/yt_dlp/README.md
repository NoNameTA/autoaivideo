# Plugin: yt_dlp

Adapter `media.download` — tải media bằng [yt-dlp](https://github.com/yt-dlp/yt-dlp) (OSS, miễn phí; SPEC 06 cli-process, 14 free-only).

- **inputs.url** hoặc **config.url**: URL tải.
- **config.args** (tuỳ chọn): đối số bổ sung (vd `-f`, `--max-filesize`).
- **config.output_template**: mẫu tên file (mặc định `%(title).80s.%(ext)s`).

Chạy qua `python -m yt_dlp`. File tải về nằm trong thư mục output của step → thành asset.

> Người vận hành chịu trách nhiệm tuân thủ ToS của nguồn (SPEC 14 §7).
