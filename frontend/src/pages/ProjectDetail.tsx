import { Link, useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { useProject } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { fmtDate } from "../lib/format";

export function ProjectDetail() {
  const { id = "" } = useParams();
  const { data, isLoading, isError, error } = useProject(id);

  return (
    <SectionPanel
      title={data ? data.name : "Dự án"}
      description="Chi tiết dự án + tạo lô sản xuất."
      spec="SPEC 03 §3"
    >
      {isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {isError && (
        <p className="text-sm text-danger">Lỗi: {(error as ApiError)?.message}</p>
      )}
      {data && (
        <div className="flex flex-col gap-3">
          <div className="text-sm text-muted">{data.description || "Không có mô tả"}</div>
          <div className="text-sm">
            Pipeline mặc định: <span className="font-mono">{data.default_pipeline}</span>
          </div>
          <div className="text-xs text-muted">Tạo: {fmtDate(data.created_at)}</div>
          <div>
            <Link
              to={`/projects/${data.id}/batches/new`}
              className="inline-block rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
            >
              + Tạo lô (Batch)
            </Link>
          </div>
        </div>
      )}
    </SectionPanel>
  );
}
