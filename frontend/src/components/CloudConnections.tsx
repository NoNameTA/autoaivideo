import { useState } from "react";

import { ApiError } from "../api/client";
import {
  useConnections,
  useCreateConnection,
  useCreateCredential,
  useCredentials,
  useDeleteConnection,
  useDeleteCredential,
  useTestConnection,
} from "../api/hooks";
import { useUiStore } from "../store/ui";
import { fmtDate } from "../lib/format";

const INPUT = "w-full rounded border border-border bg-bg px-2 py-1 text-sm text-text";
const SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets";
const SHEETS_CAPS = [
  "cloud.google_sheets.read",
  "cloud.google_sheets.write",
  "cloud.google_sheets.append",
  "cloud.google_sheets.update_cell",
  "cloud.google_sheets.update_row",
];

const HEALTH: Record<string, string> = {
  connected: "text-success",
  error: "text-danger",
  disabled: "text-muted",
  unknown: "text-warning",
};

export function CloudConnections() {
  const creds = useCredentials();
  const conns = useConnections();
  const createCred = useCreateCredential();
  const delCred = useDeleteCredential();
  const createConn = useCreateConnection();
  const delConn = useDeleteConnection();
  const testConn = useTestConnection();
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  // Form Credential (giá trị mặc định cấu hình được — KHÔNG hard-code trong adapter).
  const [cName, setCName] = useState("Google chính");
  const [cPath, setCPath] = useState(".secrets/gsa.json");

  // Form Connection.
  const [dName, setDName] = useState("Sheet của tôi");
  const [credId, setCredId] = useState("");
  const [spreadsheetId, setSpreadsheetId] = useState("");
  const [worksheet, setWorksheet] = useState("");

  const addCredential = () => {
    createCred.mutate(
      {
        provider: "google_sheets",
        connection_name: cName.trim(),
        authentication_type: "service_account",
        scopes: [SHEETS_SCOPE],
        secret_path: cPath.trim(),
      },
      { onSuccess: () => push("success", "Đã tạo credential"), onError: onErr },
    );
  };

  const addConnection = () => {
    createConn.mutate(
      {
        provider: "google_sheets",
        credential_id: credId || null,
        display_name: dName.trim(),
        capabilities: SHEETS_CAPS,
        settings: { spreadsheet_id: spreadsheetId.trim(), worksheet: worksheet.trim() },
      },
      { onSuccess: () => push("success", "Đã tạo connection"), onError: onErr },
    );
  };

  const runTest = (id: string) => {
    testConn.mutate(id, {
      onSuccess: (r) => push(r.ok ? "success" : "error", r.message),
      onError: onErr,
    });
  };

  return (
    <div className="mt-8 border-t border-border pt-6">
      <h2 className="mb-1 text-lg font-semibold text-text">Cloud Connections (Google Sheets)</h2>
      <p className="mb-4 text-xs text-muted">
        Credential Store + Connection Manager (SPEC 06 §10, 11 §3). Bí mật KHÔNG bao giờ hiển thị.
        Spreadsheet ID / Worksheet cấu hình tại đây — không cần sửa code.
      </p>

      {/* ----- Credentials ----- */}
      <div className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-text">Credentials</h3>
        <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-3">
          <input className={INPUT} value={cName} onChange={(e) => setCName(e.target.value)}
            placeholder="Tên credential" />
          <input className={INPUT} value={cPath} onChange={(e) => setCPath(e.target.value)}
            placeholder="Đường dẫn file bí mật (gitignored)" />
          <button
            onClick={addCredential}
            disabled={createCred.isPending}
            className="rounded bg-primary px-3 py-1 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
          >
            + Thêm credential (service_account)
          </button>
        </div>
        {creds.data && creds.data.length > 0 ? (
          <ul className="divide-y divide-border/60 rounded border border-border">
            {creds.data.map((c) => (
              <li key={c.id} className="flex items-center gap-2 px-3 py-1.5 text-sm">
                <span className="font-medium text-text">{c.connection_name}</span>
                <span className="text-xs text-muted">
                  {c.provider} · {c.authentication_type} · {c.status}
                </span>
                <button
                  onClick={() =>
                    delCred.mutate(c.id, {
                      onSuccess: () => push("success", "Đã xoá"),
                      onError: onErr,
                    })
                  }
                  className="ml-auto text-xs text-danger hover:underline"
                >
                  Xoá
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted">Chưa có credential. Đặt file bí mật rồi thêm ở trên.</p>
        )}
      </div>

      {/* ----- Connections ----- */}
      <div>
        <h3 className="mb-2 text-sm font-semibold text-text">Connections</h3>
        <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-2">
          <input className={INPUT} value={dName} onChange={(e) => setDName(e.target.value)}
            placeholder="Tên hiển thị connection" />
          <select className={INPUT} value={credId} onChange={(e) => setCredId(e.target.value)}>
            <option value="">— Chọn credential —</option>
            {(creds.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>{c.connection_name}</option>
            ))}
          </select>
          <input className={INPUT} value={spreadsheetId}
            onChange={(e) => setSpreadsheetId(e.target.value)} placeholder="Spreadsheet ID" />
          <input className={INPUT} value={worksheet} onChange={(e) => setWorksheet(e.target.value)}
            placeholder="Worksheet Name (trống = sheet đầu)" />
          <button
            onClick={addConnection}
            disabled={createConn.isPending}
            className="rounded bg-primary px-3 py-1 text-sm text-white hover:bg-primary-hover disabled:opacity-50 md:col-span-2"
          >
            + Thêm connection
          </button>
        </div>

        {conns.isLoading && <p className="text-xs text-muted">Đang tải…</p>}
        {conns.data && conns.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-muted">
                <tr className="border-b border-border">
                  <th className="py-2 pr-3">Tên</th>
                  <th className="py-2 pr-3">Spreadsheet</th>
                  <th className="py-2 pr-3">Worksheet</th>
                  <th className="py-2 pr-3">Trạng thái</th>
                  <th className="py-2 pr-3">Kiểm tra</th>
                  <th className="py-2 pr-3">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {conns.data.map((c) => (
                  <tr key={c.id} className="border-b border-border/50">
                    <td className="py-1.5 pr-3 text-text">{c.display_name}</td>
                    <td className="py-1.5 pr-3 font-mono text-xs text-muted">
                      {String(c.settings.spreadsheet_id ?? "—")}
                    </td>
                    <td className="py-1.5 pr-3 text-xs text-muted">
                      {String(c.settings.worksheet || "(đầu)")}
                    </td>
                    <td className={`py-1.5 pr-3 text-xs ${HEALTH[c.health_status] ?? "text-muted"}`}>
                      {c.health_status}
                      {c.last_check ? ` · ${fmtDate(c.last_check)}` : ""}
                    </td>
                    <td className="py-1.5 pr-3">
                      <button
                        onClick={() => runTest(c.id)}
                        disabled={testConn.isPending && testConn.variables === c.id}
                        className="rounded border border-border px-2 py-0.5 text-xs text-text hover:bg-border disabled:opacity-50"
                      >
                        {testConn.isPending && testConn.variables === c.id
                          ? "Đang test…"
                          : "Test Connection"}
                      </button>
                    </td>
                    <td className="py-1.5 pr-3">
                      <button
                        onClick={() =>
                          delConn.mutate(c.id, {
                            onSuccess: () => push("success", "Đã xoá"),
                            onError: onErr,
                          })
                        }
                        className="text-xs text-danger hover:underline"
                      >
                        Xoá
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-muted">Chưa có connection.</p>
        )}
      </div>
    </div>
  );
}
