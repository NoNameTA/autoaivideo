// Kho hướng dẫn TẬP TRUNG (mở rộng: thêm 1 mục ở đây là có hướng dẫn, KHÔNG sửa component).
// Mỗi mục LUÔN có 2 phần: `usage` (Cách sử dụng — từng bước) và `purpose` (Tác dụng).
// Nội dung bám đúng chức năng THẬT của hệ thống — không mô tả tính năng chưa có.

export interface Guide {
  title: string;
  usage: string[];
  purpose: string;
}

export const GUIDES: Record<string, Guide> = {
  // ---------- Trang chính ----------
  dashboard: {
    title: "Bảng điều khiển",
    usage: [
      "Mở khi vừa vào web để xem nhanh tình hình tổng quát.",
      "Xem số job đang chạy / hoàn tất / lỗi và hoạt động gần đây.",
      "Bấm vào mục liên quan để đi tới trang chi tiết.",
    ],
    purpose:
      "Cho cái nhìn tổng quan toàn hệ thống (job, agent, hoạt động realtime) để biết mọi thứ có đang chạy bình thường không. Dùng làm điểm bắt đầu mỗi phiên làm việc.",
  },
  projects: {
    title: "Dự án",
    usage: [
      "Tạo dự án để gom các lô (batch) và job cùng mục đích.",
      "Bấm vào một dự án để xem các lô và job bên trong.",
      "Thường không cần tạo tay — Video Sources tự dùng dự án mặc định.",
    ],
    purpose:
      "Đơn vị tổ chức cao nhất, gom nhóm công việc theo dự án. Liên kết tới Lô (Batch) → Job → Bước (Step). Bỏ qua được nếu chỉ dùng luồng Video Sources.",
  },
  workflow: {
    title: "Quy trình (Workflow)",
    usage: [
      "Xem danh sách pipeline (quy trình xử lý) hiện có: tải video, biến thể ffmpeg, chỉnh BVS…",
      "Mỗi pipeline gồm các bước (step) gắn với một capability của plugin.",
      "Thường chạy quy trình từ trang Nguồn video bằng nút ▶ Chạy quy trình.",
    ],
    purpose:
      "Định nghĩa CÁCH xử lý video (các bước nối nhau). Backend tạo job theo pipeline, Hàng đợi điều phối, Desktop Agent thực thi. Là 'công thức' cho mọi tác vụ tự động.",
  },
  queue: {
    title: "Hàng đợi (Queue)",
    usage: [
      "Theo dõi các job đang chờ / đang chạy / hoàn tất / lỗi theo thời gian thực.",
      "Xem thanh tiến độ %, tốc độ tải và ETA của job đang chạy.",
      "Bấm vào job để xem chi tiết từng bước.",
    ],
    purpose:
      "Bộ điều phối thực thi: quyết định job nào chạy khi nào, hiển thị tiến độ realtime. Giúp biết video đang tải/chỉnh tới đâu và phát hiện job lỗi.",
  },
  "video-sources": {
    title: "Nguồn video",
    usage: [
      "Tạo nguồn: Direct URL (dán link) hoặc Google Sheets (đọc từ trang tính).",
      "Nhập/Import link → bấm ▶ Chạy quy trình để tải video về máy.",
      "Chọn video ĐÃ TẢI (cột Media = 🎥) rồi Tạo biến thể hoặc Chỉnh bằng BVS.",
    ],
    purpose:
      "Cửa ngõ đưa video vào hệ thống. Quản lý danh sách link, tải về thư mục trên máy, theo dõi trạng thái và loại media. Là nơi bắt đầu hầu hết công việc.",
  },
  logs: {
    title: "Nhật ký (Logs)",
    usage: [
      "Xem các sự kiện hệ thống: tải video, cookie, media check, write-back…",
      "Lọc theo mức độ (info/cảnh báo/lỗi), nhóm, hoặc tìm theo từ khoá.",
      "Dùng khi cần biết vì sao một job lỗi.",
    ],
    purpose:
      "Lưu vết mọi hoạt động để chẩn đoán sự cố. KHÔNG ghi nội dung nhạy cảm (cookie/token). Là công cụ chính khi cần tìm nguyên nhân lỗi.",
  },
  statistics: {
    title: "Thống kê",
    usage: [
      "Xem tổng quan: số job, tỉ lệ lỗi, thông lượng theo ngày.",
      "Xem khối Tải video, Chỉnh sửa & Export, Media Check, Cookie.",
      "Bật Tự làm mới để số liệu cập nhật định kỳ.",
    ],
    purpose:
      "Tổng hợp số liệu vận hành THẬT từ dữ liệu hệ thống để đo hiệu quả: bao nhiêu video tải/chỉnh, tỉ lệ video hợp lệ, hiệu năng từng adapter.",
  },
  "desktop-agent": {
    title: "Desktop Agent (Tác nhân máy)",
    usage: [
      "Xem agent đang kết nối, capability (khả năng) và số việc đang chạy.",
      "Agent phải Online thì mới tải/chỉnh video được.",
      "Nếu offline: kiểm tra tiến trình agent (run.py) trên máy.",
    ],
    purpose:
      "Agent là chương trình chạy trên máy Windows, là nơi DUY NHẤT thực thi tải/chỉnh video và đọc file/cookie. Web chỉ ra lệnh; Agent làm việc thật.",
  },
  plugins: {
    title: "Quản lý Plugin",
    usage: [
      "Xem các plugin (adapter) đã nạp và capability của chúng.",
      "Bật/tắt hoặc xem cấu hình (schema) từng plugin.",
      "Thêm nền tảng/khả năng mới = thêm plugin, không sửa web.",
    ],
    purpose:
      "Plugin mở rộng khả năng của Agent (tải yt-dlp, ffmpeg, BVS, Google Sheets…). Theo Adapter Framework: thêm tính năng mới chỉ cần cài thêm plugin.",
  },
  "file-manager": {
    title: "Quản lý tệp",
    usage: [
      "Duyệt thư mục được phép trên máy chạy Agent.",
      "Thêm thư mục được phép trước khi truy cập.",
      "Xem/sao chép/di chuyển/đổi tên tệp trong phạm vi cho phép.",
    ],
    purpose:
      "Cho phép thao tác tệp trên máy Agent một cách an toàn (chỉ trong thư mục được cấp phép). Hỗ trợ kiểm tra video gốc / video đã xuất.",
  },
  "external-apps": {
    title: "Ứng dụng ngoài",
    usage: [
      "Khai báo kết nối tới dịch vụ ngoài (vd Google Sheets).",
      "Tạo Credential (khoá) + Connection (kết nối) rồi Kiểm tra kết nối.",
      "Nguồn video Google Sheets sẽ dùng kết nối này.",
    ],
    purpose:
      "Quản lý tích hợp với hệ thống bên ngoài qua Cloud Adapter Framework. Khoá bí mật được mã hoá, KHÔNG lộ ra web. Mở rộng = thêm adapter.",
  },
  settings: {
    title: "Cài đặt",
    usage: [
      "Nhập Token chủ sở hữu + Địa chỉ Backend rồi Lưu (sẽ tự khoá lại).",
      "Đổi Giao diện (sáng/tối).",
      "Cấu hình Thư mục lưu video và Cookie Manager bên dưới.",
    ],
    purpose:
      "Nơi cấu hình kết nối web↔backend, giao diện, thư mục lưu trữ và cookie. Token được khoá để tránh lộ; chỉ phần hiển thị, không gửi đi nơi khác.",
  },

  // ---------- Chức năng con ----------
  realtime: {
    title: "Kết nối Realtime",
    usage: [
      "Xem chấm xanh 'Realtime đã kết nối' nghĩa là web đang nhận cập nhật tức thời.",
      "Nếu 'Realtime ngắt': web sẽ tự kết nối lại sau vài giây.",
    ],
    purpose:
      "Kênh WebSocket đẩy cập nhật (tiến độ job, log, trạng thái agent) về web ngay lập tức mà không cần tải lại trang.",
  },
  "cookie-manager": {
    title: "Cookie Manager",
    usage: [
      "Bật Cookie Manager và đặt Thư mục cookie.",
      "Mỗi nền tảng trỏ tới 1 file cookies.txt (vd tiktok.cookies.txt).",
      "Xuất cookie bằng extension 'Get cookies.txt LOCALLY' → đặt vào thư mục → bấm Kiểm tra (Test) phải hiện Hợp lệ.",
    ],
    purpose:
      "Giúp Agent tải được video cần đăng nhập (TikTok/Facebook…). Web chỉ lưu ĐƯỜNG DẪN; chỉ Agent đọc nội dung cookie; không log/commit nội dung. Tự nhận file mới, không cần khởi động lại Agent.",
  },
  "output-folders": {
    title: "Thư mục lưu video (Output Folders)",
    usage: [
      "Đặt Thư mục tải về, Thư mục Export và Thư mục tạm.",
      "Bấm Lưu — Agent sẽ lưu video vào đúng thư mục này.",
      "Để trống = dùng mặc định.",
    ],
    purpose:
      "Quy định video lưu Ở ĐÂU trên máy (KHÔNG upload, không cloud). Video tải về vào Thư mục tải; video đã chỉnh/Export vào Thư mục Export.",
  },
  "cloud-connections": {
    title: "Kết nối Cloud",
    usage: [
      "Tạo Credential từ file khoá (vd Service Account JSON của Google).",
      "Tạo Connection trỏ tới credential + thông tin dịch vụ.",
      "Bấm Kiểm tra kết nối để xác nhận.",
    ],
    purpose:
      "Cấu hình kết nối tới dịch vụ đám mây (Google Sheets) theo SPEC Cloud Adapter. Khoá bí mật được cấp JIT cho Agent khi cần, không lộ ra web.",
  },
  credentials: {
    title: "Khoá bí mật (Credentials)",
    usage: [
      "Tạo credential bằng cách cung cấp đường dẫn/khoá bí mật.",
      "Dùng credential này khi tạo Connection.",
      "Web KHÔNG bao giờ hiển thị lại giá trị bí mật.",
    ],
    purpose:
      "Lưu khoá truy cập dịch vụ ngoài một cách an toàn (mã hoá). Tách riêng khoá khỏi cấu hình kết nối để bảo mật.",
  },
  "google-sheets": {
    title: "Nguồn Google Sheets",
    usage: [
      "Chọn Kết nối, nhập Spreadsheet ID + Worksheet + cột chứa link.",
      "Bấm Kiểm tra kết nối → Đọc Sheet (xem trước) → Import.",
      "Bật Tự đồng bộ để tự nạp video mới; bật Write-back để ghi kết quả ngược lại Sheet.",
    ],
    purpose:
      "Nạp hàng loạt link video từ một trang tính Google. Tự loại trùng (dedup). Có thể ghi kết quả (Trạng thái, Output Path, Media Type…) trở lại đúng dòng trong Sheet.",
  },
  "media-type": {
    title: "Loại media (Media Check)",
    usage: [
      "Sau khi tải xong, hệ thống tự kiểm tra file bằng ffprobe.",
      "🎥 Video = có hình (chỉnh được); 🎵 Audio = chỉ tiếng; ❌ Invalid = hỏng/thiếu file.",
      "Dùng bộ lọc Media để xem từng loại.",
    ],
    purpose:
      "Phân biệt video THẬT (có hình) với file chỉ-audio dựa trên luồng (stream) thực tế, không theo đuôi tên file. Ngăn đưa nhầm file audio vào bước chỉnh sửa.",
  },
  "output-path": {
    title: "Output Path (đường dẫn kết quả)",
    usage: [
      "Cột Output hiện tên file video đã tải/đã chỉnh trên máy.",
      "Rê chuột để xem đường dẫn đầy đủ.",
      "Chỉ hiện với file là 🎥 Video (audio/hỏng sẽ không có).",
    ],
    purpose:
      "Cho biết video nằm Ở ĐÂU trên máy Windows (KHÔNG upload, không tạo URL). Là cách quản lý kết quả sau khi tải/Export.",
  },
  variations: {
    title: "Tạo biến thể",
    usage: [
      "Tick chọn video ĐÃ TẢI (Media = 🎥).",
      "Đặt Số bản và chọn Spin / Đổi tỉ lệ / Caption.",
      "Bấm 'Tạo biến thể' — mỗi bản là 1 job ffmpeg, kết quả vào Thư mục Export.",
    ],
    purpose:
      "Từ 1 video gốc tạo ra N bản khác nhau (đổi tốc độ/lật/zoom/màu/tỉ lệ) để tránh trùng lặp khi đăng nhiều nơi. Dùng ffmpeg, nhanh.",
  },
  "bvs-edit": {
    title: "Chỉnh bằng Bulk Video Studio",
    usage: [
      "Tick chọn video ĐÃ TẢI (Media = 🎥).",
      "(Tuỳ chọn) mở Tuỳ chỉnh BVS để đặt logo/intro/outro/nhạc/tốc độ.",
      "Bấm 'Chỉnh bằng BVS' — Agent tự mở BVS render, kết quả vào Thư mục Export.",
    ],
    purpose:
      "Chỉnh video chuyên sâu bằng bộ công cụ Bulk Video Studio (reels, logo, nhạc, phụ đề…). Kỹ hơn biến thể ffmpeg nhưng chậm hơn. Cần BVS đã cài trên máy.",
  },
  "run-workflow": {
    title: "Chạy quy trình",
    usage: [
      "Tick chọn các video muốn xử lý (bỏ trống = tất cả).",
      "Bấm ▶ Chạy quy trình.",
      "Theo dõi tiến độ ở Hàng đợi; video tải về Thư mục tải.",
    ],
    purpose:
      "Bắt đầu tải các link đã chọn về máy. Tạo job theo pipeline, Agent thực thi bằng yt-dlp (tự dùng cookie nếu có).",
  },
  "test-connection": {
    title: "Kiểm tra kết nối",
    usage: [
      "Bấm sau khi đã chọn Kết nối + nhập Spreadsheet ID.",
      "Kết quả 'connected' nghĩa là đọc được trang tính.",
    ],
    purpose:
      "Xác nhận credential/connection hợp lệ và đọc được Sheet trước khi Import — tránh lỗi lúc chạy thật.",
  },
  "auto-sync": {
    title: "Tự đồng bộ",
    usage: [
      "Bật Tự đồng bộ và đặt chu kỳ.",
      "(Tuỳ chọn) bật Tải luôn để tự tải video mới.",
      "Bấm Lưu cấu hình.",
    ],
    purpose:
      "Tự quét Google Sheet định kỳ, chỉ nạp video MỚI (dedup bỏ video cũ). Phù hợp khi Sheet được cập nhật liên tục.",
  },
  writeback: {
    title: "Ghi kết quả về Sheet (Write-back)",
    usage: [
      "Bật Write-back ở nguồn Google Sheets.",
      "Chạy quy trình như bình thường.",
      "Sau khi job xong, hệ thống tự ghi kết quả vào đúng dòng trong Sheet.",
    ],
    purpose:
      "Ghi ngược kết quả (Trạng thái, Media Type, Output Path, Thời gian, Lỗi) về trang tính. KHÔNG tạo Output URL (video lưu trên máy). Tự thêm cột nếu thiếu, không đụng cột khác.",
  },
};
