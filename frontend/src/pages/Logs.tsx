import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import { useLogs } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { fmtDate } from "../lib/format";
import { useUiStore } from "../store/ui";
import type { LogEntry, LogLevel } from "../types/api";

const LEVELS: (LogLevel | "")[] = ["", "error", "warn", "info", "debug"];
const CATEGORIES = ["", "job", "step", "plugin", "agent", "fs", "system"];

const LEVEL_STYLE: Record<LogLevel, { color: string; icon: string }> = {
  error: { color: "text-danger", icon: "✕" },
  warn: { color: "text-warning", icon: "⚠" },
  info: { color: "text-info", icon: "•" },
  debug: { color: "text-muted", icon: "·" },
};

function levelStyle(level: string) {
  return LEVEL_STYLE[level as LogLevel] ?? { color: "text-muted", icon: "•" };
}

/** Tóm tắt phần `data` của log thành chuỗi ngắn gọn (bỏ các khoá đã hiển thị riêng). */
function summarize(data: Record<string, unknown>): string {
  const skip = new Set(["job_id", "batch_id", "project_id"]);
  return Object.entries(data)
    .filter(([k, v]) => !skip.has(k) && v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : v}`)
    .join(" · ");
}

export function Logs() {
  const [level, setLevel] = useState<LogLevel | "">("");
  const [category, setCategory] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const wsConnected = useUiStore((s) => s.wsConnected);

  // Debounce ô tìm kiếm.
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const logs = useLogs({
    level: level || undefined,
    category: category || undefined,
    search: search || undefined,
    limit: 200,
  });

  const rows = logs.data ?? [];
  const counts = rows.reduce<Record<string, number>>((acc, r) => {
    acc[r.level] = (acc[r.level] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <SectionPanel
      title="Nhật ký (Logs)"
      help="logs"
      description="Nhật ký hệ thống realtime — lọc theo mức độ / nhóm / tìm kiếm (SPEC 04 §7, 10 §2)."
      spec="SPEC 04 §7, 10 §2, 11 §6"
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {LEVELS.map((lv) => (
          <button
            key={lv || "all"}
            onClick={() => setLevel(lv)}
            className={`rounded px-3 py-1 text-xs ${
              level === lv ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
            }`}
          >
            {lv || "tất cả"}
            {lv && counts[lv] ? ` (${counts[lv]})` : ""}
          </button>
        ))}

        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded border border-border bg-bg px-2 py-1 text-xs text-text"
        >
          {CATEGORIES.map((c) => (
            <option key={c || "all"} value={c}>
              {c || "mọi nhóm"}
            </option>
          ))}
        </select>

        <input
          className="ml-auto w-64 rounded border border-border bg-bg px-3 py-1 text-sm text-text"
          placeholder="Tìm theo trace_id / batch / project / loại…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <span
          className={`text-xs ${wsConnected ? "text-success" : "text-muted"}`}
          title={wsConnected ? "Realtime đang kết nối" : "Mất kết nối realtime"}
        >
          {wsConnected ? "● trực tiếp" : "○ ngắt"}
        </span>
        <button
          onClick={() => logs.refetch()}
          className="rounded border border-border px-3 py-1 text-xs text-text hover:bg-border"
        >
          ↻
        </button>
      </div>

      {logs.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {logs.isError && (
        <p className="text-sm text-danger">Lỗi: {(logs.error as ApiError)?.message}</p>
      )}
      {logs.data && rows.length === 0 && (
        <p className="text-sm text-muted">
          Chưa có log nào khớp bộ lọc. Log sinh ra khi job chạy, plugin hoạt động hoặc có
          sự kiện file.
        </p>
      )}

      {rows.length > 0 && (
        <div className="max-h-[70vh] overflow-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface text-left text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-3">Thời gian</th>
                <th className="py-2 pr-3">Mức</th>
                <th className="py-2 pr-3">Nhóm</th>
                <th className="py-2 pr-3">Loại</th>
                <th className="py-2 pr-3">Đối tượng</th>
                <th className="py-2 pr-3">Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <LogRow key={r.id} row={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionPanel>
  );
}

function LogRow({ row }: { row: LogEntry }) {
  const style = levelStyle(row.level);
  const jobId = row.data.job_id as string | undefined;
  const batchId = row.data.batch_id as string | undefined;
  const detail = summarize(row.data);

  return (
    <tr className="border-b border-border/50 align-top">
      <td className="py-1.5 pr-3 text-xs text-muted whitespace-nowrap">
        {fmtDate(row.created_at)}
      </td>
      <td className={`py-1.5 pr-3 text-xs font-medium ${style.color}`}>
        {style.icon} {row.level}
      </td>
      <td className="py-1.5 pr-3 text-xs text-muted">{row.category}</td>
      <td className="py-1.5 pr-3 font-mono text-xs text-text">{row.type}</td>
      <td className="py-1.5 pr-3 text-xs">
        {jobId ? (
          <Link to={`/jobs/${jobId}`} className="font-mono text-primary hover:underline">
            {jobId.slice(0, 12)}…
          </Link>
        ) : batchId ? (
          <Link to={`/batches/${batchId}`} className="font-mono text-primary hover:underline">
            {batchId.slice(0, 12)}…
          </Link>
        ) : (
          <span className="font-mono text-muted">{row.entity_id || "—"}</span>
        )}
      </td>
      <td className="py-1.5 pr-3 text-xs text-muted break-all">{detail || "—"}</td>
    </tr>
  );
}
