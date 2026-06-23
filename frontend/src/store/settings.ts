import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light";

interface SettingsState {
  // Token chủ sở hữu (SPEC 11) — lưu localStorage để gắn vào API/WS.
  token: string;
  // Base URL backend; rỗng = same-origin (dev dùng proxy Vite).
  apiBase: string;
  theme: Theme;
  // Khóa hiển thị/sửa Owner Token + API Base URL ở trang Settings (chỉ ảnh hưởng UI Settings,
  // KHÔNG đổi cách token/apiBase được lưu hay dùng ở nơi khác).
  locked: boolean;
  setToken: (token: string) => void;
  setApiBase: (apiBase: string) => void;
  setTheme: (theme: Theme) => void;
  setLocked: (locked: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      token: "",
      apiBase: "",
      theme: "dark",
      locked: false,
      setToken: (token) => set({ token }),
      setApiBase: (apiBase) => set({ apiBase }),
      setTheme: (theme) => set({ theme }),
      setLocked: (locked) => set({ locked }),
    }),
    { name: "aivideo-settings" },
  ),
);
