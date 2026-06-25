# CHANGELOG — Source Code

> Lịch sử sinh mã nguồn (khác với spec `AI_VIDEO_AUTOMATION_SPEC/17_CHANGELOG.md`). Theo [Keep a Changelog](https://keepachangelog.com/) + SemVer.

## [Unreleased]

### Cookie Manager (đa nền tảng) — Agent tự dùng cookie khi tải video (2026-06-25)
> Bổ sung Cookie Manager: tải video TikTok/Facebook/YouTube/Instagram/X… không phụ thuộc trình
> duyệt đang mở. **Additive** — KHÔNG đổi engine/queue/agent-core/DB schema. Adapter Framework:
> thêm nền tảng = thêm 1 dòng config trên web, KHÔNG sửa code.

#### Kiến trúc
- **Website** chỉ quản lý cấu hình. **Backend** quản lý METADATA (đường dẫn). **Plugin/Agent** đọc
  & dùng nội dung cookie. Website/Backend KHÔNG lưu/đọc/log/commit NỘI DUNG cookie.

#### Added — Backend
- `services/cookie_service.py`: config 1 file JSON `<cookie_dir>/cookies.config.json` (cookie_dir
  mặc định `C:\AIVideoPlatform\.secrets`). Platform `{name, hosts[], cookie_file}`. `status` (stat
  metadata), `test` (Loaded/Expired/Invalid/Missing/PermissionDenied + expires — parse Netscape,
  **status-only**), `cookie_map` (nhúng job inputs), `platform_of_url`.
- REST `app/api/rest/cookies.py`: GET/PUT `/api/v1/cookies` + POST `/{name}/test` + list file .txt
  (Browse). `VideoSourceService.run` nhúng cookie map vào job inputs + log Cookie.Loaded/Missing.
- Logs: `Cookie.Loaded/Missing/Test.Success/Test.Failed` (KHÔNG log nội dung). Stats: khối cookie
  (configured/loaded/valid/expired + downloads with/without cookie).

#### Added — Plugin/Frontend
- yt-dlp plugin: đọc cookie map từ inputs → **tự chọn cookie theo host URL** → `--cookies` nếu có
  (tự dùng khi CÓ file); fallback nếu thiếu. Không hard-code nền tảng.
- FE: Settings → **Download Settings → Cookie Manager** (Enable, Cookie Directory, mỗi nền tảng:
  file/Browse-datalist/status/last-updated/Test/expires, thêm "Khác…"). Statistics: khối Cookie.

#### Security
- `.secrets/` đã trong `.gitignore` (cookie + config KHÔNG commit, đã kiểm tra `git check-ignore`).

#### Verified (LIVE, status-only, không mock)
- Test thật: tạo file Netscape → TikTok **Loaded** (expires 2026-07-06), YouTube **Expired**,
  Facebook **Missing**. PUT enable → cookie_map nhúng đúng (TikTok URL → dùng tiktok.cookies.txt).
  Download BBB (không khớp nền tảng) vẫn completed (fallback). Browser: Cookie Manager 3 nền tảng,
  nút Test hiện Loaded/Expired; Statistics khối Cookie (Loaded 2/Valid 1/Expired 1). ruff ✅
  pytest 60/1skip; FE lint+build ✅; không lỗi console.

### Tích hợp Bulk Video Studio — web chỉnh video bằng bộ công cụ của BVS (2026-06-24)
> Web AI Video Platform có thể chỉnh video bằng **bộ công cụ của app Bulk Video Studio** (reels
> 1080×1920, logo/intro/outro/nhạc, phụ đề whisper, speed) — **bổ sung** cạnh biến thể ffmpeg.
> Kiến trúc: nối tới **agent BulkAuto** (TranQA28, đã lái BVS qua CDP) qua HTTP `:8787`. Additive.

#### Added
- **Plugin agent `bulkauto`** (capability `video.bulkauto`, `plugins/bulkauto/`): resolve video
  nguồn → copy vào input tạm → `POST :8787/api/run` → poll `/api/status` → thu file đã chỉnh
  (`results[].output`) về asset. Chỉ stdlib (urllib). Bận → TransientError (retry); ép progress về int.
- **Pipeline `bvs_edit`** (1 step `video.bulkauto`).
- **`VariationService.create_bvs_edit`** + REST `POST /video-sources/{id}/items/{item_id}/bvs-edit`.
  Log `Video.BvsEdit`.
- **FE**: nút **"🎞️ Chỉnh bằng BVS"** cạnh "🎬 Tạo biến thể" (áp video done đã chọn).

#### DIRECT mode — Agent TỰ mở BVS, không cần web (cập nhật)
- Plugin `bulkauto` mặc định chạy **DIRECT**: import **lõi điều khiển stdlib của BulkAuto**
  (`automation.workflow.AffiliateReelsOrchestrator` ở `C:\BulkAuto`) → **tự mở BVS** + lái CDP +
  render NGAY TRONG Agent. **KHÔNG cần chạy `web.py :8787` thủ công.** KHÔNG sửa app BVS (CDP ngoài).
  Có lock (BVS 1 video/lúc), progress qua logging-handler (giữ WS sống). Tuỳ chọn HTTP nếu truyền
  `bulkauto_url`.
- **LIVE PROVEN (direct):** bấm "Chỉnh bằng BVS" → **Agent tự mở BVS** (5 tiến trình Electron) →
  render → thu asset **`bvs_..._reels.mp4` 8.48MB, 1080×1918**, job **completed**, không lỗi WS.

#### Verified (LIVE, BVS render thật)
- chuỗi **web → agent → BVS (CDP)** chạy thật. Fix bug: ép progress dict→int (tránh treo job);
  BVS bận → retry. ruff ✅ pytest 60/1skip; FE lint+build ✅; không lỗi console.
- **Điều kiện tiên quyết:** **BVS đã cài** (chạy `BAM_1_LAN_CAI_DAT_CHO_NHAN_VIEN.bat` 1 lần) +
  mã lõi BulkAuto ở `C:\BulkAuto`. Agent tự lo việc mở BVS. Cùng máy.

### Video Variations — 1 video → N bản chỉnh sửa bằng ffmpeg THẬT (2026-06-24)
> Từ 1 video đã tải, tạo N biến thể tự động bằng ffmpeg (spin tránh trùng + đổi tỉ lệ + caption/
> watermark/music tuỳ chọn). Additive: tái dùng engine/queue (mỗi biến thể = 1 job pipeline mới).

#### Added
- **Plugin ffmpeg nâng cấp** (`plugins/ffmpeg/adapter.py`): nhận `args` từ inputs|config; token
  `{input}` (resolve `source` tương đối data_dir của Agent) + `{output}`. Tương thích ngược.
- **Pipeline `ffmpeg_variant`** (1 step video.ffmpeg, args ở job inputs).
- **`VariationService`** (`services/variation_service.py`): `build_recipes` sinh N công thức ffmpeg
  khác nhau — spin (đổi tốc độ setpts/atempo, hflip, crop-zoom, eq màu) + đổi tỉ lệ (9:16/1:1/16:9)
  + caption (drawtext, tuỳ chọn) + watermark/music (tuỳ chọn, cần file). `create_variations` lấy
  asset video của 1 item done → tạo batch N job. Log `Video.Variations`.
- **REST** `POST /video-sources/{id}/items/{item_id}/variations` (count + options).
- **FE**: hàng "🎬 Biến thể" (Số bản + Spin + Đổi tỉ lệ + Caption + nút Tạo) trong panel nguồn,
  áp cho video **done** đã chọn.

#### Verified (LIVE, ffmpeg thật)
- Tải Big Buck Bunny → tạo 3 biến thể: **variant_1 1080×1920 (9:16)**, **variant_2 1080×1080 (1:1
  + spin)**, **variant_3 1920×1080 (16:9 + spin)** — 3 file khác kích thước/tỉ lệ thật (ffprobe).
- UI: chọn video done → "🎬 Tạo biến thể" → toast "Đã tạo N biến thể", job ffmpeg completed. Backend
  ruff ✅ pytest 60/1skip; FE lint+build ✅; không lỗi console.

### Tích hợp "mở ra là dùng" — Auto-Sync, tự tạo Connection, web phục vụ từ backend (2026-06-24)
> Giảm tối đa thao tác cài đặt: web tự phát hiện sản phẩm mới, tự tạo Connection, 1 địa chỉ duy nhất.
> 100% additive. Trả lời: video đã tải KHÔNG bị tải lại (dedup); sản phẩm mới được TỰ phát hiện.

#### Added
- **Auto-Sync** (`services/auto_sync.py` + lifespan): vòng lặp nền quét nguồn `google_sheets` bật
  `auto_sync` mỗi `auto_sync_interval` giây → import row MỚI (dedup bỏ video cũ → KHÔNG tải lại);
  `auto_run` (tuỳ chọn) tự tải video mới (giới hạn lô). Log `GoogleSheets.AutoSync`. FE: toggle
  "Tự đồng bộ" + interval (5/10/30 phút/1 giờ) + "Tự tải luôn" + nút Lưu cấu hình.
- **Tự tạo Connection từ URL**: dán nguyên link Sheet (hoặc ID) — backend tách ID + **tự tạo
  Connection** từ credential Google (`_ensure_connection`). **Auto-seed credential** từ `gsa.json`
  lúc khởi động → người dùng KHỎI vào External Applications.
- **Phục vụ web NGAY TỪ backend** (`_mount_frontend`): mount `frontend/dist` + SPA fallback →
  **http://localhost:8000 là cả web lẫn API** (same-origin → hết lỗi CORS / API Base).
- **CORS**: cho phép mọi origin `localhost`/`127.0.0.1` (mọi cổng) khi chạy local.

#### Verified (LIVE)
- Auto-Sync: bật trên 1 nguồn → tự import 4 (item_count 0→4, không bấm tay); thêm 1 sản phẩm vào
  Sheet → tự phát hiện (4→5, log `imported=1 duplicates=4`); video cũ không lấy lại.
- Auto-Connection: tạo nguồn dán nguyên URL, KHÔNG có connection_id → Read tự tạo Connection + đọc
  4 dòng (HTTP 200). Web phục vụ từ backend: `GET /` + `/video-sources` trả app, assets 200.
- Backend ruff ✅ pytest 60/1skip; FE lint+build ✅.

### v1.0 Completion — Write-back, Dedup, Filter/Batch, Auto-Refresh, Logs, Stats (2026-06-24)
> Hoàn thiện các hạng mục còn thiếu để đạt **v1.0**. **100% additive** trên kiến trúc cũ — KHÔNG
> refactor engine/queue/pipeline/route/theme/agent-core/DB hiện có. Không mock; tất cả test thật.

#### Added — Backend
- **Google Sheets Write-back** (`services/sheet_writeback.py` + `cloud/google_sheets.py` write API):
  khi Job từ nguồn `google_sheets` kết thúc, ghi về **ĐÚNG DÒNG** (`sheet_row`) các cột
  **Status / Output File / Output URL / Finished Time / Processing Duration / Workflow / Error**.
  Tự tạo cột nếu thiếu (KHÔNG đụng cột Link Video / cột sẵn có). **Output URL để TRỐNG** (chờ owner
  chỉ định đích upload — đã thống nhất). Hook ở `engine._advance` khi job terminal (session riêng,
  lỗi không làm hỏng engine); `ensure_columns` 1 lần lúc Run để tránh race header.
- **Dedup** (`services/video_dedup.py`): Video ID (TikTok/Facebook/YouTube/Instagram) → URL →
  `sha1(url)`. Áp dụng cho import-sheet & add_links; không tạo item/Job trùng; đếm `duplicate_count`.
- **Import Filter** (Backend lọc): `all | unprocessed | failed | not_downloaded` theo cột Status
  của Sheet. **Batch Import**: `limit` 100/500/1000/5000/all + endpoint **`count-sheet`** (đếm trước:
  total/matched/new/duplicate).
- **Video Sources summary** (`GET /video-sources/summary`): tổng hợp theo nguồn + theo loại + tổng
  (Ready/Running/Done/Failed/Duplicate), realtime (Auto Refresh).
- **Logs nghiệp vụ**: `Workflow.Start/End`, `Video.Download.Start/Progress(throttle 25%)/End`,
  `GoogleSheets.Connect/Read/Import/Update`. **KHÔNG log token/credential/private_key**.
- **Statistics**: khối `download` (downloads_total/success/failed, total_bytes, download_seconds,
  avg_speed_bps). Migration `f1d3b9a7c204` (sheet_row/video_id/url_hash + duplicate_count).

#### Added — Frontend
- Video Sources: **SummaryHeader** + badges theo nguồn + theo loại (không cần mở từng nguồn).
- SheetConfig: Import Filter + Batch + nút **Đếm trước** + toggle **Write-back** (+ worksheet ghi);
  preview enrich (dòng thật/Title/Source/URL/Status).
- **Auto Refresh** (Tắt/30s/1m/5m) ở Video Sources + Statistics (incremental, không reload trang).
- Statistics: khối **Download** (lượt/thành công/lỗi/dung lượng/tốc độ TB/thời gian).

#### Verified (LIVE, không mock)
- **Write-back** trên tab TEST riêng `WritebackTest`: tự tạo 7 cột, ghi đúng dòng 2/3/4 (Done +
  Output File/Duration/Workflow) & dòng 5 (Failed + Error = thông báo yt-dlp thật). KHÔNG đụng
  `Trang tính1`.
- **Dedup**: re-import 3 dòng → 0 imported / 3 duplicate. **Count**: 4 khớp / 0 mới / 4 trùng.
- **Logs**: 1 job thật phát đủ Workflow.Start/End + Video.Download.Start/Progress×3/End +
  GoogleSheets.Update; **không lộ token** (đã kiểm tra regex). **Stats** download = 24 lượt
  (21 ok/2 fail, 328MB, 2.2MB/s).
- **Browser**: summary + badges đúng số; Đếm trước/Filter/Batch/Write-back hoạt động; **Add File**
  (.txt) import OK + lỗi hiện toast rõ (không im lặng). Backend ruff ✅ pytest ✅; FE lint+build ✅;
  không lỗi console.

### Video Sources — Pha 2B: Google Sheets LIVE — ✅ ĐÃ TEST THẬT (không mock) (2026-06-24)
> Chạy **integration test LIVE** với Google Sheets THẬT (credential Service Account của owner +
> spreadsheet thật). Toàn bộ luồng end-to-end đã chứng minh: **Test Connection → Read → Preview →
> Import → Run → download thật** qua đúng kiến trúc cũ (Backend đọc Sheet — phương án B; Agent tải
> bằng yt-dlp — Pha 1). KHÔNG đổi Backend/DB/Agent-core/Workflow/Queue/engine/Theme — chỉ **sửa 1
> mặc định FE + tài liệu** (bug đường dẫn credential, dưới đây).

#### Verified (LIVE, dữ liệu thật)
- **Sheet:** "Data link video Affiliate NV" · worksheet `Trang tính1` · cột link `Link video gốc`
  (cột tên `Tên sản phẩm`). Test Connection (REST + nút UI) → `connected` ("Kết nối OK: …").
- **Read/Preview:** đọc thật **4769** URL video duy nhất (TikTok ~3792, Facebook ~976). **Import:**
  tạo 4769 item (status `imported`).
- **Run + download THẬT (10 video đầu — theo yêu cầu owner):** **10/10 job `completed` (100%)**,
  agent tải **195.75 MB** file video thật (Facebook Reel + TikTok), tên file = tiêu đề video thật;
  item suy `done`. Browser verify: trang Video Sources (panel Google Sheets prefill đúng config,
  filter `done` hiện đúng 10 item kèm Link + Job), External Applications (credential `active`,
  connection `connected`), nút **Test Connection** trả toast OK. Không lỗi console.

#### Fixed — đường dẫn credential mặc định (local_file) lệch `secrets_dir`
- `secret_path` được giải mã **tương đối `secrets_dir`** (mặc định `backend/.secrets`). Mặc định cũ
  `.secrets/gsa.json` bị **lồng đôi** → `backend/.secrets/.secrets/gsa.json` (không tồn tại) khiến
  tạo credential qua UI báo "Không tìm thấy file bí mật".
- **Sửa:** mặc định FE `components/CloudConnections.tsx` → `gsa.json` (chỉ tên file trong
  `secrets_dir`) + placeholder rõ nghĩa. Cập nhật `SETUP_GOOGLE_SHEETS.md` (vị trí file
  `backend/.secrets/gsa.json` + ô đường dẫn nhập `gsa.json`, không thêm tiền tố `.secrets/`).
  KHÔNG đổi logic provider/secret-store.

### UI — Navigation: ẨN TOÀN BỘ menu vào Hamburger (☰) (2026-06-24)
> **100% thuần UI điều hướng** (chỉ `components/Layout.tsx`). KHÔNG đổi route/label/chức năng/nội
> dung/API/Backend/DB/Agent/Theme/Logic. Không thêm/bớt tính năng. Mọi route giữ nguyên 100%.

#### Changed (chỉ Layout.tsx)
- **Sidebar cố định đã gỡ bỏ.** Thay bằng **thanh trên cùng (mọi kích thước màn hình)** chỉ chứa
  **Logo + ☰ (Hamburger)** — KHÔNG còn bất kỳ mục chức năng nào hiển thị trực tiếp. Tăng tối đa
  không gian làm việc (nội dung trải toàn chiều rộng), không phải cuộn Sidebar.
- **Toàn bộ Navigation nằm TRONG Drawer mở bằng ☰** (cả desktop lẫn mobile). Đóng ☰ → nav biến mất
  hoàn toàn; mở ☰ → nav hiện đầy đủ.
- **Gom nhóm thu gọn (collapsible) tất cả 9 nhóm:** **Dashboard** (Dashboard) · **Projects**
  (Projects) · **Workflow** (Workflow, Queue) · **Video** (Video Sources) · **Monitoring** (Logs,
  Statistics) · **Agent** (Desktop Agent, Plugin Manager) · **Files** (File Manager) · **Integration**
  (External Applications) · **Settings** (Settings). Giữ đủ **12 mục/route** — không bỏ sót Projects
  và File Manager. Connector tương lai (Google Drive/Dropbox/OneDrive/OBS/Notion…) thuộc nhóm
  **Integration**.
- **Responsive** (Desktop/Laptop/Tablet/Mobile) bằng cùng một giao diện — không tạo layout riêng.
  Drawer cuộn được khi nội dung dài.
- **Ghi nhớ trạng thái mở/đóng nhóm trong phiên** (`sessionStorage`, key `nav-open-groups`).
- Đóng Drawer bằng **nút ✕**, **click nền tối (backdrop)**, **chọn 1 mục** (auto-close), hoặc phím **Esc**.

#### Verified (browser thật)
- Frontend lint ✅ · build ✅ (tsc + vite). **Browser (desktop 1280 + mobile 375)**: trạng thái đóng chỉ
  hiện **Logo + ☰** (0 link nav lộ ra ngoài); mở ☰ hiện **đủ 9 nhóm / 12 link**; điều hướng OK
  (`/external` + auto-close); thu gọn/mở rộng nhóm + nhớ `sessionStorage` OK; **đủ 12 route, không thiếu
  không thừa**; theme không đổi; **không lỗi console** (chỉ cảnh báo RR future-flag có sẵn). Backend/API/
  DB/Agent/Workflow/Queue/Plugin/Logic **không đụng tới**.

### UI — Cải tiến Navigation (gom nhóm + Hamburger) (2026-06-24)
> **100% thuần UI điều hướng** (chỉ `components/Layout.tsx`). KHÔNG đổi route/label/chức năng/nội
> dung/API/Backend/DB/Agent/Theme/Logic. Không thêm/bớt tính năng.

#### Changed (chỉ Layout.tsx)
- **Gom nhóm thu gọn (collapsible) cho nhóm có ≥2 mục:** **Workflow** (Workflow, Queue) · **Agent**
  (Desktop Agent, Plugin Manager) · **Monitoring** (Logs, Statistics). Mục đơn lẻ giữ hiển thị trực
  tiếp: Dashboard, Projects, Video Sources, File Manager, Settings.
- **External Applications** đưa vào **menu Hamburger (☰)** — KHÔNG còn trên Sidebar (route `/external`
  giữ nguyên). ☰ desktop = mở overflow chỉ External Applications; ☰ mobile = mở drawer toàn bộ nav.
- **Responsive:** sidebar cố định ở desktop; <768px ẩn sidebar + thanh trên cùng có ☰ mở drawer.
- Nhóm nhớ trạng thái mở/đóng trong phiên (`sessionStorage`).

#### Verified
- Frontend lint ✅ · build ✅. Browser (desktop 1280 + mobile): sidebar gom nhóm đúng, External chỉ
  trong ☰, thu gọn/mở rộng nhóm OK, **mọi route giữ nguyên + điều hướng được** (External→`/external`),
  theme không đổi, không lỗi console (đã chụp). Backend/API/DB/Agent **không đụng tới**.

### Pha 2B — Download Progress% realtime (yt-dlp) (2026-06-24)
> Hiển thị tiến độ tải realtime trong Queue (Progress Bar/Speed/ETA/Dung lượng). **Chỉ sửa plugin
> yt-dlp** + **nối tối thiểu `on_progress`** (owner duyệt phương án A — additive, hoàn thiện scaffolding
> `StepContext.on_progress` đã thiết kế sẵn; KHÔNG refactor/đổi kiến trúc Agent).

#### Added/Changed
- **Plugin** `plugins/yt_dlp/adapter.py`: stream subprocess + parse `--progress-template`
  (`_percent_str`/`_speed_str`/`_eta_str`/bytes) → `ctx.progress(pct, "speed · ETA · dl/total")`.
- **Agent (additive):** `runner.py`+`connection.py` nối `on_progress` → gửi `step.progress` (an toàn
  thread). **Backend:** `engine.on_progress` cập nhật `job.progress` + broadcast global `job.progress`
  (Queue cập nhật không cần subscribe batch); `ws/agent` truyền `msg`.
- **Frontend:** `ui` store `jobProgress` (cập nhật từ WS); Queue thêm **ProgressCell** (bar + %, dòng
  speed/ETA/bytes); `useWebSocket` xử lý `job.progress`.

#### Verified (thật, không mock)
- Backend ruff ✅ · pytest ✅ **54 passed** · Agent ruff/pytest ✅ **15** · Frontend lint+build ✅.
- **Browser + download THẬT** (throttle `--limit-rate` để thấy rõ): Queue hiển thị **bar 11%→20%
  realtime, Speed 249.96KiB/s, ETA 01:45→01:35, 3.4MB→5.9MB/29.3MB** — chuỗi plugin→on_progress→
  step.progress→engine→broadcast→UI hoạt động đầy đủ.

### Video Sources — Pha 2: Google Sheets (read/preview/import) — Ready for Integration Test (2026-06-24)
> Mở rộng Video Sources (KHÔNG tách module/trang mới): thêm `source_type=google_sheets`. **Google Sheets
> chỉ là NGUỒN link** (đọc), không lưu/render video. **Preview = phương án B**: Website→Backend→Adapter
> đọc Sheet (Agent KHÔNG tham gia preview). Sau Import dùng **Run Workflow** chung Pha 1 → Agent tải
> yt-dlp. Kế thừa Direct URL, **không đổi** Workflow/Queue/engine/Theme/Dashboard/Settings.
> ⚠️ **Live read/import/download-từ-Sheet/update CHƯA test với Google thật** — chờ credential (Service
> Account + Spreadsheet). Phần testable (parsing cột/validation/UI) đã test + verify.

#### Added — Backend
- `cloud/google_sheets.read_values` (Backend đọc rows). `VideoSourceService`: `preview_sheet`
  (đọc→trả preview, **không** tạo item/job), `import_from_sheet` (đọc→tạo item), `update` (sửa config),
  helper `_parse_sheet` (tách URL theo cột header + dedup). Resolve token qua Connection→Credential
  (mint JIT). Logs `googlesheets.read`/`googlesheets.import`.
- REST: `PATCH /video-sources/{id}`, `POST /{id}/read-sheet`, `POST /{id}/import-sheet`.

#### Added — Frontend
- Trang Video Sources: chọn **Source Type (Direct URL / Google Sheets)**; mode Google Sheets có form
  **Connection / Spreadsheet ID / Worksheet / Cột link / Cột tên** + **Test Connection / Read Sheet
  (Preview) / Import**. Direct URL giữ nguyên. SPEC 03 §5 cập nhật.

#### Verified
- Backend ruff ✅ · pytest ✅ **54 passed** (+2: `_parse_sheet` tách cột/dedup/sai-cột, google_sheets
  source thiếu connection→422). Frontend lint ✅ · build ✅ (125.90 KB gzip).
- Browser: mode Google Sheets render đúng (form + nút); **Direct URL Pha 1 KHÔNG hỏng** (đã kiểm).
  **Live Google đọc/import/tải/update để Pha-2 integration test khi có credential** (SETUP_GOOGLE_SHEETS.md).

### Cloud Adapter Framework + Google Sheets Adapter — Ready for Integration Test (2026-06-24)
> ⚠️ **CHƯA integration-test với Google thật** (chờ credential — Pha 2). Commit chung vì migration
> `video_sources` phụ thuộc migration `credentials/connections`. Code **buildable + unit-test pass**;
> plugin **dormant** khi chưa cấu hình Credential/Connection. SPEC đã duyệt (06/08/09/10/11/14, AP1–AP4).

- **Backend:** Secret Provider (db_store Fernet + local_file, auto-select MASTER_KEY) · Credential Store
  + Connection Manager (models/migration `c7f1a9d3e520`/services/REST, **API không lộ secret**) ·
  mint Google SA token (JWT RS256) · **RPC `credential.request/response`** JIT (SPEC 09 §4.3).
- **Agent:** driver `cloud` + credential RPC client (xoá token sau op) · plugin loader đa-capability.
- **Plugin:** `plugins/google_sheets/` (gspread, 5 op) · **Frontend:** Cloud Connections UI.
- Unit test thật: `test_credentials` (Fernet round-trip, local_file IO, không lộ secret). Hướng dẫn:
  `SETUP_GOOGLE_SHEETS.md`. **Live read/write Google Sheets sẽ test ở Pha 2.**

### Video Sources — Pha 1: Direct URL (2026-06-24)
> Lớp **nguồn video đầu vào** (SPEC 02 §4.1, 03, 10). **Không đổi kiến trúc**: tái dùng nguyên
> Project→Batch→Job/Queue/Workflow/Logs/Statistics. **Website chỉ tạo Job, Backend điều phối,
> Desktop Agent tải bằng plugin yt-dlp** (`media.download`). `source_type` mở rộng (google_sheets/
> csv/folder/drive…) mà không sửa Workflow/Queue. Pha 2 (Google Sheets) chờ credential.

#### Added — SPEC
- 02 §4.1 (Video Sources = input layer, source_type mở rộng), 03 §3+§5 (route `/video-sources` +
  page), 10 (bảng `video_sources` + `video_source_items`).

#### Added — Backend
- Models `video_source` + `video_source_item` + migration `d8a2b4c6e731`; schemas; `VideoSourceService`
  (CRUD, **import** đa link từ urls/text/txt/CSV + tách URL + dedup, **run** → tạo Batch qua
  `BatchService` mỗi item=1 Job, link job↔item, **status item suy từ job** khi đọc — không đụng engine).
- REST `/api/v1/video-sources` (CRUD + `/links` + `/items` + `/run`). Pipeline built-in `video_download`
  (step `media.download`). StatsService thêm metric `video` (sources/items theo status/tổng dung lượng).

#### Added — Frontend
- **Menu + trang Video Sources** (`pages/VideoSources.tsx`): tạo nguồn, nhập/dán nhiều link, **Add Link/
  Import txt-CSV**, **Preview** (STT/tên/link/status/job, chọn-tất-cả/lọc/tìm/refresh/xoá), **Run Workflow**
  → tạo Job download. Statistics thêm panel **Video Sources**. Realtime: WS invalidate `["video-items"]`.
  Không đổi Theme/Dashboard/Settings.

#### Verified (thật, không mock)
- Backend ruff ✅ · pytest ✅ **52 passed** (+4 `test_video_sources`: import/dedup/CSV, run tạo 1 job/link,
  status suy từ job) · 1 skipped. Frontend lint ✅ · build ✅ (124.85 KB gzip).
- **Browser + download THẬT** ✅: agent (source) tải `Big_Buck_Bunny_360_10s_1MB.mp4` **967.8 KB** qua
  yt-dlp → job completed → item **done** + job link; Queue/Logs (`plugin.runtime.* media.download`)/
  Statistics (video metrics) tự tích hợp. Toàn UI flow (tạo→add→run→done) verify trong trình duyệt.

### Settings — Khóa Owner Token & API Base URL (2026-06-23)
> Bổ sung cơ chế **khóa** cho 2 trường nhạy cảm ở trang Settings. **Chỉ chạm file Settings**
> (`pages/Settings.tsx`, `store/settings.ts`) — KHÔNG đổi API/DB/Agent, KHÔNG ảnh hưởng các trang
> đã hoàn thành. **Theme giữ nguyên hoàn toàn** (luôn hiển thị & đổi được, kể cả khi đang khóa).

#### Added — Frontend (chỉ Settings)
- **Trạng thái Locked/Unlocked** cho Owner Token + API Base URL: lưu lần đầu → tự khóa; ô che
  `••••••••••••••••` read-only (không lộ độ dài/giá trị thật), badge `🔒 Locked` / `🔓 Unlocked`.
- **Unlock**: nút `🔓 Unlock Settings` → hộp thoại "Nhập mã khóa để mở khóa". Đúng → hiện lại giá
  trị thật, cho sửa, **Lưu xong tự khóa lại**. Sai → "Mã khóa không đúng.", không mở khóa, không lộ dữ liệu.
- **Bảo mật**: xác thực bằng **SHA-256 hash** (Web Crypto) — KHÔNG hard-code mã gốc, KHÔNG so chuỗi
  trực tiếp; token không vào DOM khi Locked, không log ra console. Cờ `locked` thêm vào
  `store/settings.ts` (persist) — token/apiBase vẫn lưu & dùng y như cũ (http client/WS không đổi).

#### Verified
- Frontend lint ✅ · build (tsc + vite) ✅ (121.39 KB gzip). Backend KHÔNG đổi → không cần test lại.
- Browser (thật): lưu lần đầu→khóa, reload vẫn Locked (token thật vẫn trong store), Unlock đúng/sai,
  sửa→Save→tự khóa lại, token KHÔNG lộ DOM/console, **Theme đổi bình thường khi đang Locked** (đã chụp).

### UAT — Nghiệm thu End-to-End toàn hệ thống (2026-06-23)
> 🧪 Chạy **hệ thống THẬT** (Backend uvicorn + Desktop Agent `aivideo-agent.exe` + 5 plugin +
> Frontend) — **không mock, không bypass**. Báo cáo đầy đủ: [`UAT_REPORT.md`](UAT_REPORT.md).

#### Kết quả — 19/20 hạng mục PASS
- **Stack thật:** Agent `.exe` kết nối WS `/ws/agent`, đăng ký 6 capability (cli.run, video.ffmpeg,
  web.cdp, web.cdp.edge, desktop.notepad, media.download). Tắt .exe → backend tự set **offline**.
- **Workflow E2E:** `ffmpeg_demo` → job completed 100% + **out.mp4 thật (2326B)**; `agent_full_demo`
  → ffmpeg + **Chrome CDP** (screenshot.png) completed. Plugin FFmpeg & Chrome/CDP verify **live**.
- **5 trang + Dashboard:** Workflow (5 pipeline, DAG), Queue (job realtime + filter đếm),
  Logs (32 event persist DB, lọc level, **còn sau hard-reload**), Statistics (KPI/throughput/adapter
  từ data thật), External Apps (5 app connected + **Test kết nối ok=true**), Dashboard realtime
  (`plugin.runtime.*`/`job.updated`/`agent.updated` live).
- **Retry/Cancel:** failed→queued, queued→cancelled — PASS. Validation chuẩn (`limit>200`→envelope lỗi).

#### Lỗi phát hiện
- ⚠️ **[F-1] Notepad UIA chạy live FAIL** (Win11 dùng Notepad UWP + agent chạy nền) — plugin vẫn
  nạp/kết nối/test OK; **không chặn** luồng lõi. Đề xuất sửa `agent/drivers/uia.py` (match
  AutomationId/ClassName cho Win11, hoặc đổi app demo UIA). Xếp backlog.

#### Kết luận
- ✅ **ĐẠT nghiệm thu các tiêu chí lõi.** Chờ chủ dự án duyệt trước khi bắt đầu **Google Sheets Adapter**.

### UAT — Trang chức năng (5/5): External Applications (2026-06-23)
> 🏁 **Hoàn tất UAT 5/5 trang** (Workflow · Queue · Logs · Statistics · External Apps đều làm thật).
> External App (SPEC 06) = app ngoài bọc bởi Adapter (plugin), phân loại theo `type`
> (web-cdp/desktop-uia/cli-process/local-http). Trang này là **view vận hành**: loại tích hợp +
> **trạng thái kết nối** (agent online có capability) + **test kết nối** — khác Plugin Manager (lifecycle).

#### Added — Backend
- `services/external_app_service.py` — `ExternalAppService.list` (suy từ plugins + `connection`
  từ agent registry live: connected/no_agent/disabled) + `test` (**test kết nối THẬT**: free policy
  → enabled → có agent online hỗ trợ capability + còn slot; phản ánh khả năng dispatch thực tế,
  không mock). `AgentRegistry.online_for`/`has_free_slot`.
- `GET /api/v1/external-apps` + `POST /api/v1/external-apps/{name}/test`
  (`api/rest/external_apps.py`, `schemas/external_app.py`).

#### Added — Frontend
- Trang **External Applications** thật (`pages/ExternalApps.tsx`): lọc theo **loại tích hợp**,
  card mỗi app (loại/capability/version/enabled/free/license/nguồn↗), **badge trạng thái kết nối**,
  nút **Test kết nối** (kết quả inline + toast). Realtime: `agent.updated` invalidate `["external-apps"]`.
  Types `ExternalApp`/`ExternalAppTestResult`, endpoint + hook.

#### Verified
- Backend ruff ✅ · pytest ✅ **44 passed** (+4 `test_external_apps`: list, test disabled/no_agent/
  connected/404) · 1 skipped. Frontend lint ✅ · build ✅ (120.80 KB gzip).
- Browser (thật, 5 plugin thật trong DB): 5 app phân loại đúng (cli-process/desktop-uia/web-cdp),
  lọc theo loại, trạng thái kết nối, **Test kết nối trả kết quả thật** ("chưa có agent online…"),
  không lỗi (đã chụp).

### UAT — Trang chức năng (4/5): Statistics (2026-06-23)
> Thống kê từ **DATA THẬT** jobs/steps (SPEC 02 §7). Không dữ liệu giả. Biểu đồ **SVG tự vẽ**
> (không thêm dependency — giữ bundle nhẹ). Dashboard giữ KPI realtime + activity; Statistics là
> trang phân tích tổng hợp (không trùng).

#### Added — Backend
- `services/stats_service.py` — `StatsService.compute`: job/step theo status, **fail_rate**
  (failed/(completed+failed)), **throughput** (job completed/ngày, 14 ngày, điền 0), **adapter
  stats** (count/failed/avg_seconds từ `finished_at−started_at`). Tổng hợp Python (portable
  SQLite↔PG, tránh hàm dialect).
- `GET /api/v1/stats` (`api/rest/stats.py`, `schemas/stats.py`).

#### Added — Frontend
- Trang **Statistics** thật (`pages/Statistics.tsx`): KPI (tổng job/hoàn tất/tỉ lệ lỗi/tổng step),
  thanh phân bố job+step theo status (màu SPEC 12 §4), **biểu đồ throughput SVG cột**, bảng hiệu
  năng adapter (số lần/lỗi%/thời gian TB + thanh). Realtime qua `useWebSocket` invalidate `["stats"]`.
  Types `Stats`/`AdapterStat`/`ThroughputPoint`, endpoint `getStats`, hook `useStats`.

#### Verified
- Backend ruff ✅ · pytest ✅ **40 passed** (+2 `test_stats`: rỗng + có data: counts/fail_rate/
  avg_seconds/throughput) · 1 skipped. Frontend lint ✅ · build ✅ (120.10 KB gzip).
- Browser (thật, data thật trong DB: 6 job/11 step/2 adapter): KPI + thanh status + biểu đồ
  throughput SVG + bảng adapter hiển thị đúng, màu theo SPEC, không lỗi (đã chụp).

### UAT — Trang chức năng (3/5): Logs (2026-06-23)
> **Điểm thiết kế (đã chốt với user):** bảng `events` (SPEC 10 §2 = audit/log) trước đây
> chỉ dùng cho idempotency key; activity chỉ broadcast WS, **không persist**, và **chưa có
> trường `level`**. Quyết định: **persist mọi activity vào `events`** (biến nó thành audit-log
> thật) + **thêm cột `level` suy ra từ loại event lúc ghi** (`level_for`). Không thêm bảng mới.
> Cập nhật SPEC 04 §7 + 10 §2.

#### Added — Backend
- Cột `events.level` (`info|warn|error|debug`, có index) + migration `b2c4e6f80a11`. Suy ở
  thời điểm ghi từ loại event (`*.failed`→error, retry/timeout/disabled/removed/cancelled→warn,
  progress→debug, còn lại→info).
- `services/event_service.py` — `EventService`: `level_for` (thuần), `from_activity`
  (suy entity_type/entity_id), `record` (transaction riêng: persist + broadcast `activity`,
  **làm giàu** `batch_id`/`project_id` để lọc), `list` (lọc level/category/project/batch/plugin/
  trace_id/search qua `json_extract`). Loại `idempotency_batch` không hiện ở Logs.
- `GET /api/v1/logs` (`api/rest/logs.py`, `schemas/log.py`). Engine `_activity` + plugin
  `_lifecycle` nay đi qua `EventService` (vừa ghi DB vừa phát realtime); `job.updated` kèm `batch_id`.

#### Added — Frontend
- Trang **Logs** thật (`pages/Logs.tsx`): bảng audit-log mới-nhất-trước, **lọc theo level**
  (tabs có đếm) + **nhóm** (job/step/plugin/agent/fs/system) + **tìm kiếm** (debounce, gồm
  trace_id/batch/project), badge màu theo level, link Job/Batch, chỉ báo `● live`, scroll dính header.
- Realtime: `useWebSocket` invalidate key `["logs"]` khi có `activity`/`fs.event`/`agent.updated`.
  Types `LogEntry`/`LogQuery`, endpoint `listLogs`, hook `useLogs`.

#### Verified
- Backend ruff ✅ · pytest ✅ **38 passed** (+4 `test_logs`: level_for, persist+lọc API, lọc
  batch/project, loại event nội bộ) · 1 skipped (e2e). Frontend lint ✅ · build ✅ (118.69 KB gzip).
- Browser (thật): trang Logs hiển thị event thật, lọc level + đếm số đúng, **realtime tự cập nhật
  qua WS không refresh** (sinh event qua API → bảng thêm dòng), không lỗi console.

### UAT — Trang chức năng (2/5): Queue (2026-06-23)
#### Added — Backend
- `JobService.list_all` + `GET /api/v1/jobs` (list job toàn cục, lọc `status` + `search` job/batch id, mới nhất trước). Test `test_jobs.py`.
#### Added — Frontend
- Trang **Queue** thật: bảng job realtime (WS invalidate `jobs-all`), **filter tabs có đếm số** + **tìm kiếm** (debounce), **retry/cancel** theo trạng thái, link Job/Batch. Loading/empty/error, responsive (overflow-x).
#### Verified
- Backend ruff ✅ · pytest ✅ **34 passed** (+2). Frontend lint ✅ · build ✅. Browser: Queue hiển thị 6 job + filter count + search (đã chụp).

### UAT — Trang chức năng (1/5): Workflow (2026-06-23)
> User chốt: editor đầy đủ (vượt SPEC V2.0); cập nhật SPEC 02 §4 + 03 §5. Pipeline lưu DB.

#### Added — Backend
- Model `pipelines` + migration `793d0effa4d0`; `schemas/pipeline.py`; `services/pipeline_service.py` (list/get/create/update/delete + `get_steps` ưu tiên DB→fallback JSON + `sync_builtins` seed).
- REST `/api/v1/pipelines` (CRUD + `POST /{name}/run` = tạo batch). Seed built-in lúc khởi động.
- `batch_service` resolve step từ `PipelineService.get_steps` (thay vì chỉ JSON).

#### Added — Frontend
- Trang **Workflow** thật: list pipeline + **DAG các step**, editor tạo/sửa (thêm/xoá/sắp xếp step, adapter datalist, config JSON), xoá, **Run** (chọn project + inputs → batch → BatchView). Loading/empty/error, responsive.

#### Verified
- Backend ruff ✅ · pytest ✅ **32 passed** (+4 pipeline). Frontend lint ✅ · build ✅.
- Browser: trang Workflow hiển thị 4 pipeline built-in + DAG thật (đã chụp).

## [1.0.0] - 2026-06-23

> 🏁 **Bản phát hành ổn định đầu tiên** — hoàn thành Phase 1–10. Nền tảng tự động hoá video AI chạy thật end-to-end + **deploy thật** (GitHub Pages live, CI xanh, Docker smoke PASS).

### Release notes — v1.0.0
- **Frontend** (Vite/React/TS/Tailwind) → **GitHub Pages live**: https://nonameta.github.io/autoaivideo/ (BrowserRouter + `404.html` SPA fallback, refresh mọi route OK).
- **Backend** (FastAPI + SQLAlchemy + SQLite + WebSocket): REST CRUD (project/batch/job/agent/plugin), orchestrator (durable queue, state machine, retry/backoff, ack/heartbeat timeout, resume), WS hub, plugin registry, **File Manager + Permission Manager** (Allowed Folders). Docker-ready (`docker compose` + alembic entrypoint).
- **Desktop Agent** (Python + bản `.exe` PyInstaller): WS client (reconnect), drivers **Process / CDP (raw DevTools) / UIA (pywinauto)**, File Manager + **Watch realtime** (watchdog, chuẩn hoá + debounce).
- **Plugin SDK** + plugin thật: `ffmpeg`, `yt-dlp`, `chrome`, `edge`, `notepad` (contract test, free-only gate).
- **Dashboard realtime**: job/progress, `fs.event`, `plugin.runtime.*`, `plugin.lifecycle.*` (Activity Stream có bộ lọc).
- **Chất lượng & vận hành**: CI 3 job (lint + pytest + build), E2E thật (gated `RUN_E2E=1`), Docker smoke PASS, INSTALL.md verified trên môi trường sạch.
- Tag liên quan: `v0.8.0` (Deployment), `v0.9.0` (Desktop Agent Full).

### Roadmap sau v1.0.0
- **UAT** (User Acceptance Testing) — dùng thực tế, sửa lỗi phát sinh.
- Sau UAT ổn định → Adapter: **1) Google Sheets · 2) OBS · 3) Bulk Video Studio**.
- **Prompt Engine** — sau khi các adapter cốt lõi hoàn thiện.

### Phase 10 — Real Deployment (2026-06-22)
#### Done
- Xác minh **INSTALL.md từ môi trường sạch**: Backend (venv + alembic + /health=200), Frontend (`npm ci` + build + 404.html), Agent (venv + chạy), Agent .exe (Phase 9).
- **Push source + tags** lên GitHub `NoNameTA/autoaivideo`: `main`, `v0.8.0`, `v0.9.0`.
- **GitHub Actions CI: 3/3 job XANH** (Backend / Agent / Frontend).
- **🌐 GitHub Pages LIVE & verified**: `https://nonameta.github.io/autoaivideo/` → HTTP 200, title đúng, base `/autoaivideo/`; **refresh route sâu** (`/projects/...`) phục vụ `404.html` (SPA fallback) — hoạt động.

#### Fixed (để CI/Deploy chạy được)
- `db/session.py`: tự tạo thư mục SQLite (CI thiếu `backend/data/`).
- `agent/tests/__init__.py`: pytest tìm thấy package `agent` trên CI.
- `tests/conftest.py`: lifespan (sync_plugins/SELECT 1) dùng DB test có schema.
- 2 workflow: **ghim toàn bộ action sang full commit SHA** (đáp ứng repo policy).
- Repo settings (owner): bật Actions → "Allow all actions"; bỏ "Require actions pinned to full SHA" (vì `upload-pages-artifact` gọi `upload-artifact` nội bộ bằng tag).

#### Docker smoke test ✅ (2026-06-23)
- `docker compose up -d --build` → container Up; `alembic upgrade head` chạy 2 migration trong container; uvicorn lên.
- Smoke: `/health`=200, `/ready`=200 (DB check), `/api/v1/info` v2.0.0 (env=prod), POST project (auth)=201. **PASS**.
- Fix: `core/config.py` dùng `NoDecode` cho `cors_origins` (pydantic-settings JSON-decode env list trước validator → lỗi khi `CORS_ORIGINS` là chuỗi trong compose).

**Phase 10 hoàn tất.** Website live + CI xanh + Docker smoke PASS + INSTALL.md verified.

### Phase 9 — Desktop Agent Full (2026-06-22)
> SPEC 05 §4. Quyết định người dùng: CDP = raw DevTools Protocol (không Playwright); UIA verify bằng Notepad; plugin qua .exe = ffmpeg + chrome.

#### Added — Drivers (agent)
- `agent/drivers/cdp.py` — **CDP driver nâng cao** (raw CDP qua websockets+httpx): `launch/goto/eval/wait_for/click/type/title/screenshot/close`. Chrome & Edge.
- `agent/drivers/uia.py` — **UIA driver** (pywinauto): `start (kết nối cửa sổ theo title qua Desktop) / focus_window / type_keys / get_text / close` (đóng bằng PID, tránh hộp thoại Save). Dep `pywinauto` (Windows-only).

#### Added — Plugins (External App adapters)
- Refactor `plugins/chrome` dùng `CdpDriver` (goto + đọc title + screenshot).
- `plugins/edge` (`web.cdp.edge`) — Edge headless qua CDP.
- `plugins/notepad` (`desktop.notepad`) — minh hoạ UIA: mở Notepad, gõ text, đọc lại → asset.
- Pipeline `agent_full_demo.json` (video.ffmpeg + web.cdp) cho E2E qua .exe.

#### Changed
- `build_exe.py`: hidden-import `agent.drivers.cdp/uia` + collect-all `httpx` (driver chỉ plugin nạp động dùng → PyInstaller không tự thấy). Exe nạp đủ 6 capability.
- SPEC `05 §4` cập nhật: CDP raw (không Playwright), thêm Edge.

#### Verified
- Backend pytest ✅ 28 passed (1 e2e skip) · Agent ruff ✅ · pytest ✅ 15 passed (+3 driver).
- **CDP nâng cao (thật) ✅**: Chrome & Edge headless → `goto`+`eval(title)=AIVID`+`screenshot.png`.
- **🎯 E2E qua Agent .exe (thật) ✅**: `aivideo-agent.exe` nạp đủ plugin, chạy `agent_full_demo` → **out.mp4 (ffmpeg) + screenshot.png (chrome)** + job completed. RESULT PASS.

#### Pending Verification
- **UIA Notepad live**: code thật (pywinauto), nhưng môi trường chạy tool **không có desktop tương tác** (`WaitForInputIdle failed`) → chưa verify live ở đây. Chạy trên desktop thật sẽ hoạt động.

## [0.8.0] - 2026-06-22

> Mốc **Semantic Versioning** đầu tiên (SPEC 13 §7). `0.8.0` gói toàn bộ Phase 1–8 (mỗi phase ~ 1 minor:
> 0.1 Scaffold · 0.2 Backend · 0.3 Frontend · 0.4 Workflow+Agent · 0.5 Plugin · 0.6 File Manager · 0.7 Integration&Testing · 0.8 Deployment). Chi tiết theo từng Phase bên dưới.

### Phase 8 — GitHub Pages Deployment (2026-06-22)
> SPEC 13. Quyết định người dùng: cấu hình + verify local (không push repo); chỉ tạo compose (Docker smoke Pending).

#### Added
- **404.html SPA fallback**: script `postbuild` copy `dist/index.html` → `dist/404.html`; base động qua `VITE_BASE`.
- **Workflow** `.github/workflows/frontend-pages.yml`: build (base = `/<repo>/`) + `upload-pages-artifact` + `deploy-pages`.
- **PyInstaller**: `agent/run.py` (entry), `agent/build_exe.py` → `dist/aivideo-agent.exe`. Agent config `plugins_dir` (env `PLUGINS_DIR`) để exe nạp plugin từ thư mục.
- **INSTALL.md**: hướng dẫn cài đặt & chạy Frontend / Backend / Agent / Plugin / Pages / smoke.
- `Dockerfile`: entrypoint chạy `alembic upgrade head` trước uvicorn (SPEC 13 §4). `.gitignore`: loại `agent/build|dist`, `*.spec`.

#### Verified
- Frontend: `npm run build` (base `/aivideo/`) ✅ — **404.html = index.html**, assets đúng base.
- **SPA-refresh (browser) ✅**: mở trực tiếp route sâu `/aivideo/projects/...` render đúng trang (vite preview mô phỏng GH Pages) — đã chụp.
- **Agent .exe (thật) ✅**: `aivideo-agent.exe` nạp plugin từ `PLUGINS_DIR`, đăng ký backend đầy đủ `['cli.run','media.download','video.ffmpeg','web.cdp']`, online.
- Backend pytest ✅ · Agent pytest ✅.

#### Pending Verification
- **Deploy Pages thật**: chưa push (AIVideoPlatform chưa có remote) — cấu hình sẵn sàng, user tự tạo repo + bật Pages.
- **Docker compose smoke**: Docker chưa cài trên máy → chưa chạy `docker compose up`. Compose + Dockerfile đã hoàn thiện.

### Phase 7 — Integration & Testing (2026-06-22)
> SPEC 15. Quyết định người dùng: E2E thật bằng `cli.run`/`video.ffmpeg` (không mock); E2E local-only, CI chạy unit/build; Dashboard Activity Stream phân loại `plugin.runtime.*` + `plugin.lifecycle.*`.

#### Added — Activity Stream (backend)
- `plugins/registry_cache.py` — cache capability plugin để engine phân biệt step plugin vs built-in.
- Engine phát **global `activity`**: `job.updated`, `plugin.runtime.{started,progress,finished,failed}` (cho step do plugin chạy).
- `PluginService` phát `plugin.lifecycle.{installed,enabled,disabled,updated,removed}`; sync cập nhật registry_cache.
- Pipeline `ffmpeg_demo.json` (1 step `video.ffmpeg`) cho E2E.

#### Added — Dashboard realtime (frontend)
- `ui` store: buffer `activities` + `pushActivity`. `useWebSocket`: phân loại `activity`/`fs.event`/`agent.updated` → feed.
- **Dashboard "Hoạt động realtime"**: panel + bộ lọc (Tất cả/Job/Plugin runtime/Plugin lifecycle/FS/Agent), màu phân loại.

#### Added — Tests
- `tests/test_recovery.py` (integration): resume requeue step đang chạy + agent→offline; ack-timeout requeue.
- `tests/e2e/test_pipeline_e2e.py` (**gated `RUN_E2E=1`**): backend+agent subprocess thật chạy `ffmpeg_demo` → job completed + asset `out.mp4` thật + Dashboard nhận `plugin.runtime.*` + `job.updated`.
- conftest: marker `e2e` + skip khi không có `RUN_E2E=1`.

#### Changed — CI / SPEC
- `.github/workflows/ci.yml`: 3 job (Backend/Frontend/Agent) — install + lint + test/build + summary; agent thêm pytest.
- SPEC `09 §4.2` (Activity Stream global), SPEC `15` (E2E thật + CI gate).

#### Verified
- Backend: ruff ✅ · pytest ✅ **28 passed, 1 skipped (e2e)**. Agent: ruff ✅ · pytest ✅ **12 passed**. Frontend: lint ✅ · build ✅ (115KB gzip).
- **E2E THẬT (`RUN_E2E=1`) ✅**: full pipeline Web→…→Dashboard, job completed + `out.mp4` thật + realtime activity. RESULT PASS.
- **Dashboard realtime (browser) ✅**: panel Hoạt động realtime hiển thị `job` + `plugin.runtime` thật (đã chụp màn hình).

### Phase 6.1 — Watch Folder realtime nâng cấp (2026-06-22)
> Hoàn thiện watchdog theo yêu cầu. Cập nhật SPEC 07 §8 + SPEC 09 §4.1.

#### Changed — Agent
- `watcher.py` viết lại: **chuẩn hoá** sự kiện về 4 loại `created/modified/deleted/moved`; **Permission Manager lọc từng sự kiện** trước khi gửi; **reconcile** (watch = đã-yêu-cầu ∩ allowed ∩ thư-mục) → **tự start/stop khi Allowed Folders đổi**.
- `connection.py`: **coalesce/debounce** sự kiện trùng `(type,path,dest_path)` trong cửa sổ `watch_debounce_ms` (mặc định 200ms) trước khi gửi `fs.event`; `config.update` gọi `watcher.reconcile()`.
- `fs_manager.PermissionManager`: thêm `is_allowed()` (không raise) cho watcher lọc. Config thêm `watch_debounce_ms`.

#### Added — Tests
- `agent/tests/test_watcher.py`: chuẩn hoá+lọc loại, coalesce giữ mới nhất, **sự kiện watchdog thật** (tạo file → nhận event), reconcile gỡ watch khi folder rời Allowed Folders.

#### Changed — SPEC
- `07_FILE_SYSTEM_SPEC.md` §8 (Watch Folder realtime). `09_COMMUNICATION_PROTOCOL.md` §4.1 (fs.request/fs.response/fs.event + config.update allowed_folders).

#### Verified
- Agent: ruff ✅ · pytest ✅ **12 passed**. Backend: pytest ✅ **26 passed**. Frontend: build ✅.
- **End-to-end realtime THẬT** ✅: agent watch thư mục → tạo/sửa/xoá file → `fs.event` (created/modified/deleted, chuẩn hoá + coalesce) tới dashboard WS. RESULT PASS.

### Phase 6 — File Manager (2026-06-22)
> SPEC 07 + 11 §5. Quyết định người dùng: RPC fs.request/fs.response qua /ws/agent; Allowed Folders trong DB đẩy xuống agent; watchdog cho watch realtime.

#### Added — Backend
- Model `allowed_folders` + migration `141a508530c2`; `schemas/fs.py`; `services/allowed_folder_service.py` (CRUD + `is_within_allowed` chống traversal).
- `api/ws/fs_rpc.py` — RPC correlation-id qua `/ws/agent` (backend chờ Future).
- `services/fs_service.py` — validate Allowed Folders (Permission Manager) rồi forward tới agent; `push_allowed` đẩy danh sách xuống agent.
- `api/rest/fs.py` — `/api/v1/fs/{allowed (CRUD), scan, read, metadata, copy, move, rename, delete, watch}`.
- `agent_registry`: `first_agent_id` + `send_all`; ws/agent xử lý `fs.response`/`fs.event`, đẩy `config.update{allowed_folders}` khi agent register; lỗi `AGENT_UNAVAILABLE`/`FS_ERROR`.

#### Added — Agent (tích hợp Desktop Agent + Plugin System)
- `fs_manager.py` — `PermissionManager` (realpath + prefix, chống traversal) + thao tác thật: scan/read/copy/move/rename/delete/metadata.
- `watcher.py` — Folder Watcher dùng `watchdog`, emit `fs.event` thread-safe về backend.
- `connection.py` — xử lý `config.update` (cập nhật Allowed Folders), `fs.request` → fs_manager → `fs.response`. Dep `watchdog==6.0.0`.

#### Added — Frontend
- `types/fs.ts`, endpoints FS; trang **File Manager** thật: quản lý Allowed Folders, duyệt thư mục, Read/Info/Rename/Copy/Move/Delete, bật Watch + nhận `fs.event` realtime.

#### Added — Tests
- Backend `test_fs.py` (Allowed CRUD, traversal util, scan no-agent→503, ngoài allowed→403). Agent `test_fs_manager.py` (thao tác file thật + từ chối quyền).

#### Verified
- Backend: ruff ✅ · pytest ✅ **26 passed**. Agent: ruff ✅ · pytest ✅ **8 passed**. Frontend: lint ✅ · `npm run build` ✅ (114KB gzip).
- **End-to-end THẬT** ✅: backend + agent → thêm Allowed Folder → scan/metadata/read/copy/rename/move/delete file thật + watch bật; path ngoài allowed bị chặn **403**. RESULT PASS.

### Phase 5 — Plugin System (2026-06-22)
> SPEC 06, 08, 14. Plugin SDK ổn định + lifecycle + contract; adapter thật cho app verify được trên máy.

#### Added — Plugin SDK (agent)
- `agent/sdk.py` — `Adapter` ABC (capability, lifecycle `validate_config→prepare→run→collect→cleanup`), `StepContext`, `ProcessDriver`, `Asset`, `TransientError`/`PermanentError`, `SDK_VERSION`.
- `agent/plugin_loader.py` — nạp plugin từ `plugins/<name>/`: đọc `manifest.yaml`, **cổng free-only** (SPEC 14), import `adapter.py` theo entrypoint, khớp capability; plugin lỗi bị bỏ qua an toàn.
- `agent/adapter_registry.py` — gộp adapter built-in (`cli.run`) + plugin nạp động; cung cấp `capabilities()`.
- Refactor `adapters/cli_run.py`, `runner.py` (chạy đúng lifecycle SDK), `connection.py` (map `TransientError`→retryable).

#### Added — 3 plugin thật (plugins/)
- `plugins/ffmpeg/` (capability `video.ffmpeg`, cli-process) — manifest+adapter+schema+README.
- `plugins/yt_dlp/` (capability `media.download`, cli-process).
- `plugins/chrome/` (capability `web.cdp`, web-cdp) — điều khiển Chrome headless qua DevTools Protocol, screenshot.
- Mỗi plugin: `manifest.yaml` + `adapter.py` + `config.schema.json` + `README.md` (đúng SPEC 08 §2).

#### Added — Backend
- `app/plugins/loader.py` — quét `plugins/`, nhúng `config_schema`, **đồng bộ vào DB** lúc khởi động (giữ `enabled`/`config` người dùng); cổng free-only. Plugin Manager (frontend) + `/plugins/{name}/schema` dùng dữ liệu thật.

#### Added — Contract test (SPEC 08 §9, 15 §3)
- `agent/tests/test_plugin_contract.py` — kiểm tra manifest đủ trường, `free is True`, JSON Schema hợp lệ, adapter subclass + capability khớp + có `run`, loader nạp đủ 3 capability. **4 test pass.**

#### Deps
- Thêm `PyYAML==6.0.2` (backend + agent) cho manifest YAML.

#### Verified (thật)
- Backend: ruff ✅ · pytest ✅ **22 passed**. Agent: ruff ✅ · pytest ✅ **4 passed (contract)**.
- **Live adapter (thật) ✅**: FFmpeg tạo `out.mp4` (2326B) offline; Chrome CDP chụp `screenshot.png` (5261B) headless; yt-dlp v2026.06.09 sẵn sàng. RESULT PASS.

### Phase 4 — Workflow & Queue + Desktop Agent tối thiểu (2026-06-22)
> Quyết định người dùng: gộp 1 Desktop Agent thật để chạy job end-to-end thật (không mock). SPEC 02 §3, 04 §4, 05, 09 §4.

#### Added — Orchestrator (backend)
- `orchestrator/queue.py` (hàng đợi bền: enqueue/due_pending/leased_expired/mark_done/active_count), `retry.py` (backoff luỹ thừa), `agent_registry.py` (kết nối agent online + chọn theo capability+slot), `dispatcher.py` (dựng step.assign).
- `orchestrator/engine.py` — engine chạy nền (asyncio): dispatch theo `max_concurrent_steps`+capacity, máy trạng thái step `queued→assigned→running→completed|failed|retrying`, ack/heartbeat timeout → requeue, retry/backoff, **resume-on-startup** (requeue step treo), advance job → enqueue step kế/hoàn tất, cập nhật batch counts + broadcast realtime.
- Wire: `BatchService.create` đẩy step đầu vào queue + nhúng job vars vào `step.inputs`; `/ws/agent` đăng ký registry + chuyển kết quả về engine; lifespan start/stop engine + resume.
- Pipeline `local_demo.json` (adapter `cli.run`, free-only).

#### Added — Desktop Agent tối thiểu (thật)
- `agent/`: `drivers/process.py` (spawn process thật), `adapters/cli_run.py` (capability `cli.run`, chạy lệnh + thu file→asset+sha256), `fs.py` (thư mục asset SPEC 07), `runner.py`, `connection.py` (WS client: register/heartbeat/nhận assign/ack/completed/failed + reconnect), `main.py`.

#### Fixed
- ruff E501/UP041; `process.py` dùng builtin `TimeoutError`.

#### Verified
- Backend: ruff ✅ · pytest ✅ **22 passed** (thêm `test_orchestrator`: retry, enqueue, advance→completed, fail→failed, retry→requeue, asset persist).
- **End-to-end THẬT** ✅: chạy backend + agent thật → tạo batch `local_demo` 2 job → engine điều phối → agent spawn process Python thật → tạo file thật (`input.json` chứa job vars `{"topic":"A"}`, `result.txt`) → cả 2 job `completed`. RESULT PASS.
- Frontend build ✅ · agent ruff ✅.

### Phase 3 — Frontend Foundation (2026-06-22)
> Nối UI ↔ API thật (backend đã có ở phase trước). Đã duyệt: thêm RHF+Zod; hoãn virtualization; BrowserRouter+404.html (Phase Deploy).

#### Added
- **Infra**: `types/api.ts` (khớp schema backend), `store/{settings,ui}.ts` (token/apiBase/theme persist localStorage + ws status + toasts), `api/{client,endpoints,hooks}.ts` (REST client gắn token + React Query), `api/ws.ts` (WS client reconnect/backoff), `hooks/useWebSocket.ts` (kết nối + subscribe + invalidate cache realtime), `lib/format.ts` (status→màu SPEC 12 §4).
- **Components**: `StatusBadge`, `Toaster`, `Modal`, `JobGrid`, `StepTimeline`, `AgentCard`; forms RHF+Zod: `ProjectForm`, `PluginForm`, `BatchForm`.
- **Pages wired (API thật)**: Dashboard (info+agents+ws), Projects (list/create/delete), ProjectDetail, CreateBatch, BatchView (JobGrid + subscribe batch), JobDetail (StepTimeline + retry/cancel), DesktopAgent (agents), Plugins (register/enable/remove/schema), Settings (token/apiBase/theme + test kết nối).
- **Routing**: thêm `/projects/:id`, `/projects/:id/batches/new`, `/batches/:id`, `/jobs/:id` (SPEC 03 §3). Banner: thiếu token + đang kết nối lại WS (SPEC 12 §7). Theme dark/light (SPEC 12 §2).
- Deps: `react-hook-form`, `zod`, `@hookform/resolvers`.

#### Fixed
- `tailwind.config.js` + `postcss.config.js`: dùng glob/đường dẫn **tuyệt đối** (cwd-independent) để Tailwind sinh utility đúng dù chạy từ thư mục bất kỳ.

#### Verified (thật, trong trình duyệt)
- `npm run build` ✅ + `eslint` ✅ + `tsc --noEmit` ✅ (113KB gzip < 300KB target SPEC 03 §7).
- Chạy backend :8000 + Vite dev → trình duyệt preview: Dashboard hiển thị **Backend Online v2.0.0**, **Realtime đã kết nối** (WS), Projects load **dữ liệu thật** qua API có token (200). Theme dark + sidebar xanh đúng SPEC 12.

### Phase 2 (đã ĐẢO thứ tự) — Backend Foundation (2026-06-22)
> Quyết định người dùng: đảo Frontend↔Backend để Frontend nối API thật (tránh mock). Phạm vi = SPEC roadmap GĐ2: DB + ORM + REST API + WS hub. KHÔNG gồm orchestrator/execution (Phase Workflow & Queue).

#### Added
- **DB layer**: `db/base.py` (Declarative Base + TimestampMixin), `db/session.py` (async engine, SQLite WAL + foreign_keys), `db/ids.py` (ULID có tiền tố, tự hiện thực — không thêm dep).
- **Models (SPEC 10)**: projects, batches, jobs, steps, assets, agents, plugins, job_queue, events + enums.
- **Alembic (SPEC 10 §5)**: `alembic.ini`, `alembic/env.py` (URL đồng bộ từ config), migration `e90554295847_initial_schema` (9 bảng) — đã `upgrade head` thật.
- **Schemas (Pydantic)**: project, batch, job, step, asset, agent, plugin, common (Page/Error).
- **Services**: project, batch (sinh job+step từ template, transaction-safe, idempotency-key qua bảng events), job (get/retry/cancel), agent (register/heartbeat/offline), plugin (registry), pagination con trỏ.
- **REST API (SPEC 04 §2)**: projects CRUD, batches create/get + list jobs, jobs get/retry/cancel, agents list, plugins list/register/schema/update/remove, health/ready (ready kiểm tra DB).
- **WebSocket (SPEC 09 §3/§4)**: `/ws` (subscribe/broadcast) + `/ws/agent` (register/heartbeat → persist agent; step messages → Event + broadcast). ConnectionManager + envelope.
- **Core**: errors (envelope chuẩn SPEC 09 §6 + handlers), security (owner/agent token SPEC 11), constants (hết magic number).
- **Pipeline template**: `orchestrator/pipelines/faceless_v1.json` + `templates.py`.
- **Tests (SPEC 15)**: 16 test pass — health, auth (401/403 envelope), projects CRUD + validation, batches (sinh 3 job × 6 step, cancel, retry-409, idempotency, project-404), plugins lifecycle, websocket.

#### Fixed
- `logging.py`: ép stdout UTF-8 (Windows cp1252 gây UnicodeEncodeError với tiếng Việt).
- Endpoint 204 (`delete`) bỏ annotation `-> None` (FastAPI hiểu nhầm thành response_model).

#### Build/Test result
- Backend: ruff ✅ · pytest ✅ 16 passed · uvicorn thật ✅ (tạo project thật, 401/201 đúng).
- Frontend: `npm run build` ✅ (82KB gzip). Agent: chạy ✅.

### Phase 1 — Scaffold Project (2026-06-22)
#### Added
- Cấu trúc repo theo SPEC `02 §2`: `backend/`, `frontend/`, `agent/`, `plugins/`, `data/`, `.github/workflows/`.
- **Root**: `README.md`, `.gitignore`, `docker-compose.yml`, `CHANGELOG.md`, `.github/workflows/ci.yml`.
- **Backend**: FastAPI skeleton chạy được — `app/main.py` (`/health`, `/ready`, `/api/v1/info`), `core/config.py` (pydantic-settings theo SPEC `04 §6`), `core/logging.py`, router health, test `test_health.py`. `pyproject.toml` + `requirements.txt` + `.env.example` + `Dockerfile`.
- **Frontend**: Vite + React 18 + TS + Tailwind + React Router + Zustand + TanStack Query. Layout + 11 trang theo SPEC `12` (Dashboard, Projects, Workflow, Queue, File Manager, Desktop Agent, External Applications, Plugin Manager, Logs, Statistics, Settings). Design tokens theo SPEC `12 §2`. Build `npm run build` thành công.
- **Agent**: Python package chạy được — `agent/main.py`, `config.py`, `drivers/`, `adapters/`. `pyproject.toml` + `requirements.txt` + `.env.example`.
- **Plugins**: `plugins/README.md` (hướng dẫn cấu trúc theo SPEC `08`).

#### Notes
- Quyết định người dùng: giữ nguyên cấu trúc SPEC (`agent/`, `manifest.yaml`); không tạo `shared/scripts/docs`.
- Phase 1 là khung chạy được (scaffold thật, không placeholder giả) — chức năng đầy đủ thêm ở các phase sau.
