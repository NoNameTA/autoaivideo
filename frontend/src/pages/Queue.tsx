import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import { useCancelJob, useJobsAll, useRetryJob } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { StatusBadge } from "../components/StatusBadge";
import { fmtDate } from "../lib/format";
import { useUiStore } from "../store/ui";
import type { JobStatus } from "../types/api";

const FILTERS: (JobStatus | "")[] = ["", "queued", "running", "completed", "failed", "cancelled"];

export function Queue() {
  const [status, setStatus] = useState<JobStatus | "">("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const retry = useRetryJob();
  const cancel = useCancelJob();
  const push = useUiStore((s) => s.pushToast);
  const jobProgress = useUiStore((s) => s.jobProgress);

  // Debounce ô tìm kiếm.
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const jobs = useJobsAll(status || undefined, search || undefined);
  const onError = (e: unknown) => push("error", (e as ApiError).message);

  const counts = (jobs.data ?? []).reduce<Record<string, number>>((acc, j) => {
    acc[j.status] = (acc[j.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <SectionPanel
      title="Queue"
      description="Hàng đợi job theo thời gian thực — lọc, tìm kiếm, retry/cancel (SPEC 04 §4)."
      spec="SPEC 04 §4, 10"
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f || "all"}
            onClick={() => setStatus(f)}
            className={`rounded px-3 py-1 text-xs ${
              status === f ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
            }`}
          >
            {f || "tất cả"}
            {f && counts[f] ? ` (${counts[f]})` : ""}
          </button>
        ))}
        <input
          className="ml-auto w-56 rounded border border-border bg-bg px-3 py-1 text-sm text-text"
          placeholder="Tìm theo job id / batch id…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button
          onClick={() => jobs.refetch()}
          className="rounded border border-border px-3 py-1 text-xs text-text hover:bg-border"
        >
          ↻
        </button>
      </div>

      {jobs.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {jobs.isError && (
        <p className="text-sm text-danger">Lỗi: {(jobs.error as ApiError)?.message}</p>
      )}
      {jobs.data && jobs.data.length === 0 && (
        <p className="text-sm text-muted">Không có job nào khớp bộ lọc.</p>
      )}

      {jobs.data && jobs.data.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-3">Job</th>
                <th className="py-2 pr-3">Batch</th>
                <th className="py-2 pr-3">Pipeline</th>
                <th className="py-2 pr-3">Trạng thái</th>
                <th className="py-2 pr-3">%</th>
                <th className="py-2 pr-3">Cập nhật</th>
                <th className="py-2 pr-3">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {jobs.data.map((j) => (
                <tr key={j.id} className="border-b border-border/50">
                  <td className="py-1.5 pr-3">
                    <Link to={`/jobs/${j.id}`} className="font-mono text-xs text-primary hover:underline">
                      {j.id.slice(0, 14)}…
                    </Link>
                  </td>
                  <td className="py-1.5 pr-3">
                    <Link to={`/batches/${j.batch_id}`} className="font-mono text-xs text-muted hover:underline">
                      {j.batch_id.slice(0, 12)}…
                    </Link>
                  </td>
                  <td className="py-1.5 pr-3 text-xs text-muted">{j.pipeline}</td>
                  <td className="py-1.5 pr-3"><StatusBadge status={j.status} /></td>
                  <td className="py-1.5 pr-3">
                    <ProgressCell
                      pct={jobProgress[j.id]?.pct ?? j.progress}
                      msg={j.status === "running" ? jobProgress[j.id]?.msg : undefined}
                    />
                  </td>
                  <td className="py-1.5 pr-3 text-xs text-muted">{fmtDate(j.updated_at)}</td>
                  <td className="py-1.5 pr-3">
                    <div className="flex gap-2 text-xs">
                      <button
                        disabled={!["failed", "cancelled"].includes(j.status)}
                        onClick={() =>
                          retry.mutate(j.id, {
                            onSuccess: () => push("success", "Đã retry"),
                            onError,
                          })
                        }
                        className="text-warning hover:underline disabled:opacity-30"
                      >
                        Retry
                      </button>
                      <button
                        disabled={["completed", "cancelled"].includes(j.status)}
                        onClick={() =>
                          cancel.mutate(j.id, {
                            onSuccess: () => push("success", "Đã huỷ"),
                            onError,
                          })
                        }
                        className="text-danger hover:underline disabled:opacity-30"
                      >
                        Huỷ
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionPanel>
  );
}

function ProgressCell({ pct, msg }: { pct: number; msg?: string }) {
  return (
    <div className="w-32">
      <div className="flex items-center gap-1">
        <div className="h-1.5 flex-1 overflow-hidden rounded bg-border">
          <div className="h-full rounded bg-primary transition-all" style={{ width: `${pct}%` }} />
        </div>
        <span className="w-9 shrink-0 text-right text-xs text-muted">{pct}%</span>
      </div>
      {msg && <div className="mt-0.5 truncate text-[10px] text-muted" title={msg}>{msg}</div>}
    </div>
  );
}
