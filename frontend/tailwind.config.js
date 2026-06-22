import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Glob tuyệt đối theo vị trí file config -> không phụ thuộc thư mục chạy (cwd).
const root = dirname(fileURLToPath(import.meta.url));

/** @type {import('tailwindcss').Config} */
// Bảng màu theo SPEC 12 §2 (dark-first, đen + xanh dương), map sang CSS variables.
export default {
  content: [join(root, "index.html"), join(root, "src/**/*.{ts,tsx}")],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        border: "var(--border)",
        primary: "var(--primary)",
        "primary-hover": "var(--primary-hover)",
        text: "var(--text)",
        muted: "var(--text-muted)",
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
        info: "var(--info)",
      },
      borderRadius: { DEFAULT: "8px" },
    },
  },
  plugins: [],
};
