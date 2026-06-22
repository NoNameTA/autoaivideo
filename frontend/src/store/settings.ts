import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light";

interface SettingsState {
  // Token chủ sở hữu (SPEC 11) — lưu localStorage để gắn vào API/WS.
  token: string;
  // Base URL backend; rỗng = same-origin (dev dùng proxy Vite).
  apiBase: string;
  theme: Theme;
  setToken: (token: string) => void;
  setApiBase: (apiBase: string) => void;
  setTheme: (theme: Theme) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      token: "",
      apiBase: "",
      theme: "dark",
      setToken: (token) => set({ token }),
      setApiBase: (apiBase) => set({ apiBase }),
      setTheme: (theme) => set({ theme }),
    }),
    { name: "aivideo-settings" },
  ),
);
