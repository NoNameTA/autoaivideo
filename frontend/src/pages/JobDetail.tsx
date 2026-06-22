import { useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { useCancelJob, useJob, useRetryJob } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { StatusBadge } from "../components/StatusBadge";
import { StepTimeline } from "../components/StepTimeline";
import { useUiStore } from "../store/ui";

export function JobDetail() {
  const { id = "" } = useParams();
  const { data, isLoading, isError, error } = useJob(id);
  const retry = useRetryJob();
  const cancel = useCancelJob();
  const push = useUiStore((s) => s.pushToast);

  const onError = (e: unknown) => push("error", (e as ApiError).message);

  return (
    <SectionPanel
      title="Chi tiết Job"
      description="Timeline step + thao tác (SPEC 12 §5)."
      spec="SPEC 03 §3"
    >
      {isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {isError && <p className="text-sm text-danger">Lỗi: {(error as ApiError)?.message}</p>}
      {data && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <StatusBadge status={data.status} />
            <span className="font-mono text-xs text-muted">{data.id}</span>
            <span className="text-sm text-muted">{data.pipeline}</span>
          </div>
          {data.error && <div className="text-sm text-danger">{data.error}</div>}

          <div className="flex gap-2">
            <button
              onClick={() =>
                retry.mutate(data.id, {
                  onSuccess: () => push("success", "Đã đưa job về hàng đợi"),
                  onError,
                })
              }
              className="rounded bg-warning px-3 py-1.5 text-sm text-black hover:opacity-90"
            >
              Retry
            </button>
            <button
              onClick={() =>
                cancel.mutate(data.id, {
                  onSuccess: () => push("success", "Đã huỷ job"),
                  onError,
                })
              }
              className="rounded bg-danger px-3 py-1.5 text-sm text-white hover:opacity-90"
            >
              Huỷ
            </button>
          </div>

          <StepTimeline steps={data.steps} />
        </div>
      )}
    </SectionPanel>
  );
}
