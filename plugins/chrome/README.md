# Plugin: chrome

Adapter `web.cdp` — điều khiển Chrome headless qua **Chrome DevTools Protocol** (SPEC 05 §4 CDP, 06 web-cdp).

- **inputs.url** hoặc **config.url**: URL điều hướng.
- **config.wait_ms**: thời gian chờ tải trang (mặc định 1500ms).
- **config.chrome_path** (tuỳ chọn): đường dẫn `chrome.exe` nếu không tự dò được.

Hành vi: mở Chrome `--headless=new --remote-debugging-port=<free>`, `Page.navigate` tới URL, chụp `Page.captureScreenshot` → lưu `screenshot.png` vào thư mục output của step.

Không hard-code toạ độ chuột (SPEC 06). Yêu cầu Chrome cài sẵn (miễn phí).
