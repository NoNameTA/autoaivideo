# Plugin: edge

Adapter `web.cdp.edge` — điều khiển Microsoft Edge headless qua Chrome DevTools Protocol (cùng `CdpDriver` với plugin chrome). SPEC 05 §4, 06 web-cdp.

- **inputs.url** / **config.url**: URL điều hướng.
- **config.browser_path**: đường dẫn `msedge.exe` nếu không tự dò.

Hành vi: mở Edge `--headless=new`, `goto` URL, đọc `title` (eval), chụp `screenshot.png` + ghi `page.json`. Yêu cầu Edge cài sẵn (miễn phí).
