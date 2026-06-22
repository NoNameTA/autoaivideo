import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import autoprefixer from "autoprefixer";
import tailwindcss from "tailwindcss";

// Trỏ tuyệt đối tới tailwind.config.js -> không phụ thuộc thư mục chạy (cwd).
const root = dirname(fileURLToPath(import.meta.url));

export default {
  plugins: [tailwindcss({ config: join(root, "tailwind.config.js") }), autoprefixer()],
};
