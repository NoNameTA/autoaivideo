import { Link } from "react-router-dom";
import type { Job } from "../types/api";
import { StatusBadge } from "./StatusBadge";

// Lưới job (SPEC 03 §5, 12 §5). Virtualization hoãn theo quyết định (thêm khi cần với batch lớn).
export function JobGrid({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return <p className="text-sm text-muted">Chưa có job nào.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-muted">
          <tr className="border-b border-border">
            <th className="py-2 pr-4">#</th>
            <th className="py-2 pr-4">Job</th>
            <th className="py-2 pr-4">Trạng thái</th>
            <th className="py-2 pr-4">Tiến độ</th>
            <th className="py-2 pr-4"></th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="border-b border-border/60">
              <td className="py-2 pr-4 text-muted">{job.seq}</td>
              <td className="py-2 pr-4 font-mono text-xs">{job.id}</td>
              <td className="py-2 pr-4">
                <StatusBadge status={job.status} />
              </td>
              <td className="py-2 pr-4">{job.progress}%</td>
              <td className="py-2 pr-4">
                <Link to={`/jobs/${job.id}`} className="text-primary hover:underline">
                  Chi tiết
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
