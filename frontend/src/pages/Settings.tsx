import { useState } from "react";

import { ApiError } from "../api/client";
import { endpoints } from "../api/endpoints";
import { SectionPanel } from "../components/SectionPanel";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-text";

export function Settings() {
  const settings = useSettingsStore();
  const push = useUiStore((s) => s.pushToast);

  const [token, setToken] = useState(settings.token);
  const [apiBase, setApiBase] = useState(settings.apiBase);

  const save = () => {
    settings.setToken(token.trim());
    settings.setApiBase(apiBase.trim());
    push("success", "Đã lưu cài đặt");
  };

  const testConnection = async () => {
    settings.setToken(token.trim());
    settings.setApiBase(apiBase.trim());
    try {
      const info = await endpoints.info();
      push("success", `Kết nối OK: ${info.name} v${info.version}`);
    } catch (e) {
      push("error", `Kết nối lỗi: ${(e as ApiError).message}`);
    }
  };

  return (
    <SectionPanel
      title="Settings"
      description="Token, đường dẫn backend, theme (SPEC 03 §3, 11)."
      spec="SPEC 11 §3, 12 §2"
    >
      <div className="flex max-w-xl flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Owner Token
          <input
            type="password"
            className={INPUT}
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="change-me-owner-token"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          API Base URL (trống = same-origin / proxy dev)
          <input
            className={INPUT}
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
            placeholder="http://localhost:8000"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Theme
          <select
            className={INPUT}
            value={settings.theme}
            onChange={(e) => settings.setTheme(e.target.value as "dark" | "light")}
          >
            <option value="dark">Tối</option>
            <option value="light">Sáng</option>
          </select>
        </label>
        <div className="flex gap-2">
          <button
            onClick={save}
            className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
          >
            Lưu
          </button>
          <button
            onClick={testConnection}
            className="rounded border border-border px-4 py-2 text-sm text-text hover:bg-border"
          >
            Kiểm tra kết nối
          </button>
        </div>
      </div>
    </SectionPanel>
  );
}
