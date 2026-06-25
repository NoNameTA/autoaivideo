import { useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { useCookies, useSaveCookies, useTestCookie } from "../api/hooks";
import { useUiStore } from "../store/ui";
import type { CookiePlatform } from "../types/api";

const INPUT = "w-full rounded border border-border bg-bg px-2 py-1 text-sm text-text";

const STATUS_DOT: Record<string, string> = {
  valid: "text-success",
  loaded: "text-success",
  missing: "text-muted",
  expired: "text-danger",
  invalid: "text-danger",
  permission_denied: "text-warning",
  authentication_failed: "text-danger",
};
const STATUS_LABEL: Record<string, string> = {
  valid: "Valid",
  loaded: "Loaded",
  missing: "Missing",
  expired: "Expired",
  invalid: "Invalid",
  permission_denied: "Permission Denied",
  authentication_failed: "Authentication Failed",
};

interface Row extends CookiePlatform {
  testStatus?: string;
  testMsg?: string;
  testSource?: string;
  expires?: string;
}

export function CookieManager() {
  const cookies = useCookies();
  const save = useSaveCookies();
  const test = useTestCookie();
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const [enabled, setEnabled] = useState(false);
  const [cookieDir, setCookieDir] = useState("");
  const [rows, setRows] = useState<Row[]>([]);

  // Khởi tạo từ config đã lưu.
  useEffect(() => {
    if (cookies.data) {
      setEnabled(cookies.data.enabled);
      setCookieDir(cookies.data.cookie_dir);
      setRows(cookies.data.platforms.map((p) => ({ ...p })));
    }
  }, [cookies.data]);

  const files = cookies.data?.cookie_files ?? [];

  const setRow = (i: number, patch: Partial<Row>) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  const addRow = () =>
    setRows((prev) => [...prev, { name: "", hosts: [], cookie_file: "", test_url: "" }]);

  const removeRow = (i: number) => setRows((prev) => prev.filter((_, idx) => idx !== i));

  const onSave = () => {
    save.mutate(
      {
        enabled,
        cookie_dir: cookieDir.trim(),
        platforms: rows
          .filter((r) => r.name.trim())
          .map((r) => ({
            name: r.name.trim(),
            hosts: r.hosts,
            cookie_file: r.cookie_file.trim(),
            test_url: (r.test_url || "").trim(),
          })),
      },
      {
        onSuccess: () => push("success", "Đã lưu Cookie Manager"),
        onError: onErr,
      },
    );
  };

  const onTest = (i: number) => {
    const name = rows[i].name;
    test.mutate(name, {
      onSuccess: (r) =>
        setRow(i, { testStatus: r.status, testMsg: r.message, expires: r.expires, testSource: r.source }),
      onError: onErr,
    });
  };

  // Hướng dẫn xuất cookie khi nền tảng còn thiếu (status missing) — KHÔNG đọc/lưu nội dung cookie.
  const missing = rows.filter((r) => r.name.trim() && (r.status ?? "missing") === "missing");

  return (
    <div className="rounded-lg border border-border bg-surface/40 p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-semibold text-text">Cookie Manager (đa nền tảng)</span>
        <label className="flex items-center gap-2 text-sm text-text">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          Enable
        </label>
      </div>
      <p className="mb-3 text-xs text-muted">
        Plugin yt-dlp tự chọn cookie theo nền tảng khi tải (TikTok/Facebook/YouTube…). Web chỉ lưu
        ĐƯỜNG DẪN — không lưu/đọc nội dung cookie.
      </p>

      <label className="mb-3 flex flex-col gap-1 text-sm">
        Cookie Directory
        <input
          className={INPUT}
          value={cookieDir}
          onChange={(e) => setCookieDir(e.target.value)}
          placeholder="C:\AIVideoPlatform\.secrets"
        />
      </label>

      {/* datalist gợi ý file .txt trong cookie_dir (Browse) */}
      <datalist id="cookie-files">
        {files.map((f) => (
          <option key={f} value={f} />
        ))}
      </datalist>

      <div className="space-y-2">
        {rows.map((r, i) => (
          <div key={i} className="rounded border border-border bg-bg p-2">
            <div className="grid grid-cols-1 gap-2 md:grid-cols-12">
              <input
                className={`${INPUT} md:col-span-2`}
                value={r.name}
                onChange={(e) => setRow(i, { name: e.target.value })}
                placeholder="Platform"
              />
              <input
                className={`${INPUT} md:col-span-3`}
                value={r.hosts.join(", ")}
                onChange={(e) =>
                  setRow(i, { hosts: e.target.value.split(",").map((h) => h.trim()).filter(Boolean) })
                }
                placeholder="hosts (vd tiktok.com)"
              />
              <input
                className={`${INPUT} md:col-span-4`}
                list="cookie-files"
                value={r.cookie_file}
                onChange={(e) => setRow(i, { cookie_file: e.target.value })}
                placeholder="cookie file (vd tiktok.cookies.txt) — Browse"
              />
              <div className="flex items-center gap-1 text-xs md:col-span-2">
                <span className={STATUS_DOT[r.status ?? "missing"] ?? "text-muted"}>●</span>
                <span className="text-muted">
                  {STATUS_LABEL[r.status ?? "missing"] ?? r.status}
                  {r.last_updated ? ` · ${r.last_updated}` : ""}
                </span>
              </div>
              <div className="flex items-center gap-2 md:col-span-1">
                <button
                  onClick={() => onTest(i)}
                  disabled={test.isPending || !r.name}
                  className="rounded border border-border px-2 py-1 text-xs text-text hover:bg-border disabled:opacity-50"
                >
                  Test
                </button>
                <button
                  onClick={() => removeRow(i)}
                  className="text-xs text-danger hover:underline"
                >
                  Xoá
                </button>
              </div>
            </div>
            <input
              className={`${INPUT} mt-2`}
              value={r.test_url ?? ""}
              onChange={(e) => setRow(i, { test_url: e.target.value })}
              placeholder="Test URL (tuỳ chọn) — URL 1 video để Agent test cookie THẬT (live --simulate)"
            />
            {r.testStatus && (
              <div className="mt-1 text-xs">
                <span className={STATUS_DOT[r.testStatus] ?? "text-muted"}>
                  {STATUS_LABEL[r.testStatus] ?? r.testStatus}
                </span>
                <span className="text-muted">
                  {" "}
                  — {r.testMsg}
                  {r.expires ? ` · hết hạn ${r.expires}` : ""}
                  {r.testSource ? ` · ${r.testSource === "agent" ? "Agent (thật)" : "Backend"}` : ""}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Hướng dẫn xuất cookie khi còn thiếu — KHÔNG đọc/lưu nội dung cookie */}
      {missing.length > 0 && (
        <div className="mt-3 rounded border border-warning/40 bg-warning/10 p-3 text-xs text-text">
          <div className="mb-1 font-semibold text-warning">
            ⚠️ Chưa có cookie cho: {missing.map((m) => m.name).join(", ")} — hướng dẫn lấy cookie thật:
          </div>
          <ol className="ml-4 list-decimal space-y-0.5 text-muted">
            <li>Đăng nhập nền tảng (vd TikTok) trên trình duyệt.</li>
            <li>Cài extension <b>Get cookies.txt LOCALLY</b> (Chrome/Edge Web Store).</li>
            <li>Mở trang nền tảng (đã đăng nhập) → bấm extension → <b>Export</b>.</li>
            <li>Lưu/đổi tên file đúng (vd <code>tiktok.cookies.txt</code>).</li>
            <li>
              Đặt vào thư mục: <code>{cookieDir || "C:\\AIVideoPlatform\\.secrets"}</code>
            </li>
          </ol>
          <div className="mt-1 text-muted">
            Xong → Desktop Agent tự phát hiện (không cần restart) → bấm <b>Test</b> phải hiện{" "}
            <span className="text-success">Valid</span>.
          </div>
        </div>
      )}

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={onSave}
          disabled={save.isPending}
          className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
        >
          💾 Lưu Cookie Manager
        </button>
        <button
          onClick={addRow}
          className="rounded border border-border px-3 py-2 text-sm text-text hover:bg-border"
        >
          + Thêm nền tảng (Khác…)
        </button>
        <span className="text-xs text-muted">Lưu trước rồi Test (Test đọc cấu hình đã lưu).</span>
      </div>
    </div>
  );
}
