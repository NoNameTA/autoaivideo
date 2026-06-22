import { useState } from "react";
import { useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { useBatch, useBatchJobs } from "../api/hooks";
import { JobGrid } from "../components/JobGrid";
import { SectionPanel } from "../components/SectionPanel";
import { StatusBadge } from "../components/StatusBadge";
import { useSubscribe } from "../hooks/useWebSocket";
import type { JobStatus } from "../types/api";

const FILTERS: (JobStatus | "")[] = ["", "queued", "running", "completed", "failed", "cancelled"];

export function BatchView() {
  const { id = "" } = useParams();
  const [status, setStatus] = useState<JobStatus | "">("");
  useSubscribe("batch", id);

  const batch = useBatch(id);
  const jobs = useBatchJobs(id, status || undefined);

  return (
    <SectionPanel
      title="Theo dõi Batch"
      description="Lưới job + trạng thái realtime (SPEC 12 §5)."
      spec="SPEC 03 §3"
    >
      {batch.isError && (
        <p className="text-sm text-danger">Lỗi: {(batch.error as ApiError)?.message}</p>
      )}
      {batch.data && (
        <div className="mb-4 flex items-center gap-4">
          <StatusBadge status={batch.data.status} />
          <span className="text-sm text-muted">{batch.data.input_count} job</span>
          <div className="flex gap-3 text-sm">
            {Object.entries(batch.data.counts).map(([k, v]) => (
              <span key={k} className="text-muted">
                {k}: <span className="text-text">{v}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mb-3 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f || "all"}
            onClick={() => setStatus(f)}
            className={`rounded px-3 py-1 text-xs ${
              status === f ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
            }`}
          >
            {f || "tất cả"}
          </button>
        ))}
      </div>

      {jobs.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {jobs.data && <JobGrid jobs={jobs.data.items} />}
    </SectionPanel>
  );
}
