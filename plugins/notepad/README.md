# Plugin: notepad

Adapter `desktop.notepad` — minh hoạ **UI Automation** (pywinauto, SPEC 05 §4, 06 desktop-uia).

- **inputs.text** / **config.text**: văn bản gõ vào Notepad (mặc định "AI Video Platform").

Hành vi: mở `notepad.exe`, focus cửa sổ, **gõ văn bản thật** vào control, đọc lại nội dung, ghi `notepad.txt` (asset). Không hard-code toạ độ chuột. Yêu cầu Windows + pywinauto.
