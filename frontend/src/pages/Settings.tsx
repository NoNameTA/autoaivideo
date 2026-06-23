import { useState } from "react";

import { ApiError } from "../api/client";
import { endpoints } from "../api/endpoints";
import { Modal } from "../components/Modal";
import { SectionPanel } from "../components/SectionPanel";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-text";
// Chuỗi che cố định (không phản ánh độ dài giá trị thật) cho trạng thái Locked.
const MASK = "••••••••••••••••";
// SHA-256 của mã khóa mở Settings — KHÔNG lưu mã gốc; xác thực bằng cách hash đầu vào rồi so hash.
const UNLOCK_HASH = "521f0a08b734797b631279a2d04e939bd1d481a3c02634fe2e01cdcfac742038";

async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function Settings() {
  const settings = useSettingsStore();
  const push = useUiStore((s) => s.pushToast);

  // editable = đang ở chế độ nhập/sửa (lần đầu chưa khóa, hoặc đã mở khóa tạm thời).
  const [unlocked, setUnlocked] = useState(false);
  const editable = !settings.locked || unlocked;

  const [token, setToken] = useState(settings.token);
  const [apiBase, setApiBase] = useState(settings.apiBase);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [code, setCode] = useState("");
  const [codeError, setCodeError] = useState("");

  const save = () => {
    settings.setToken(token.trim());
    settings.setApiBase(apiBase.trim());
    // Lưu xong: tự khóa lại (cả lần đầu lẫn sau khi sửa).
    settings.setLocked(true);
    setUnlocked(false);
    push("success", "Đã lưu cài đặt — đã khóa Owner Token & API Base URL");
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

  const openUnlock = () => {
    setCode("");
    setCodeError("");
    setDialogOpen(true);
  };

  const submitUnlock = async () => {
    const ok = (await sha256Hex(code)) === UNLOCK_HASH;
    if (!ok) {
      setCodeError("Mã khóa không đúng.");
      return;
    }
    // Đúng: nạp lại giá trị thật từ store để sửa, mở khóa tạm thời.
    setToken(settings.token);
    setApiBase(settings.apiBase);
    setUnlocked(true);
    setDialogOpen(false);
    setCode("");
    push("success", "Đã mở khóa Settings");
  };

  return (
    <SectionPanel
      title="Settings"
      description="Token, đường dẫn backend, theme (SPEC 03 §3, 11)."
      spec="SPEC 11 §3, 12 §2"
    >
      <div className="flex max-w-xl flex-col gap-4">
        {/* ----- Phần khóa: Owner Token + API Base URL ----- */}
        <div className="rounded-lg border border-border bg-surface/40 p-4 transition-all">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-text">Kết nối Backend</span>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs transition-colors ${
                editable ? "bg-success/15 text-success" : "bg-border text-muted"
              }`}
            >
              {editable ? "🔓 Unlocked" : "🔒 Locked"}
            </span>
          </div>

          <div className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Owner Token
              {editable ? (
                <input
                  type="password"
                  className={INPUT}
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="change-me-owner-token"
                  autoComplete="off"
                />
              ) : (
                <input className={`${INPUT} text-muted`} value={MASK} readOnly tabIndex={-1} />
              )}
            </label>

            <label className="flex flex-col gap-1 text-sm">
              API Base URL (trống = same-origin / proxy dev)
              {editable ? (
                <input
                  className={INPUT}
                  value={apiBase}
                  onChange={(e) => setApiBase(e.target.value)}
                  placeholder="http://localhost:8000"
                  autoComplete="off"
                />
              ) : (
                <input className={`${INPUT} text-muted`} value={MASK} readOnly tabIndex={-1} />
              )}
            </label>

            {editable ? (
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
            ) : (
              <div>
                <button
                  onClick={openUnlock}
                  className="rounded border border-border px-4 py-2 text-sm text-text hover:bg-border"
                >
                  🔓 Unlock Settings
                </button>
              </div>
            )}
          </div>
        </div>

        {/* ----- Theme: GIỮ NGUYÊN, luôn hiển thị & đổi được ----- */}
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
      </div>

      {/* ----- Hộp thoại nhập mã khóa ----- */}
      <Modal open={dialogOpen} title="Mở khóa Settings" onClose={() => setDialogOpen(false)}>
        <div className="flex flex-col gap-3">
          <p className="text-sm text-muted">Nhập mã khóa để mở khóa</p>
          <input
            type="password"
            autoFocus
            autoComplete="off"
            className={INPUT}
            value={code}
            onChange={(e) => {
              setCode(e.target.value);
              if (codeError) setCodeError("");
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitUnlock();
            }}
            placeholder="Mã khóa"
          />
          {codeError && <p className="text-sm text-danger">{codeError}</p>}
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setDialogOpen(false)}
              className="rounded border border-border px-4 py-2 text-sm text-text hover:bg-border"
            >
              Hủy
            </button>
            <button
              onClick={submitUnlock}
              className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
            >
              Mở khóa
            </button>
          </div>
        </div>
      </Modal>
    </SectionPanel>
  );
}
