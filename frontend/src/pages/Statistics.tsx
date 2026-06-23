import { ApiError } from "../api/client";
import { useStats } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { fmtDate } from "../lib/format";
import { useUiStore } from "../store/ui";
import type { AdapterStat, Stats, ThroughputPoint } from "../types/api";

const STATUS_VAR: Record<string, string> = {
  queued: "var(--text-muted)",
  assigned: "var(--info)",
  running: "var(--info)",
  completed: "var(--success)",
  failed: "var(--danger)",
  retrying: "var(--warning)",
  cancelled: "var(--text-muted)",
};

function statusVar(status: string): string {
  return STATUS_VAR[status] ?? "var(--text-muted)";
}

function fmtSeconds(s: number): string {
  if (s <= 0) return "—";
  return s < 60 ? `${s.toFixed(1)}s` : `${(s / 60).toFixed(1)}m`;
}

function Kpi({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold" style={{ color: accent ?? "var(--text)" }}>
        {value}
      </div>
    </div>
  );
}

/** Phân bố job theo trạng thái — thanh ngang tỉ lệ. */
function StatusBars({ byStatus, total }: { byStatus: Record<string, number>; total: number }) {
  const entries = Object.entries(byStatus).filter(([, n]) => n > 0);
  if (entries.length === 0) {
    return <p className="text-sm text-muted">Chưa có job nào.</p>;
  }
  return (
    <div className="space-y-2">
      {entries.map(([status, n]) => {
        const pct = total ? Math.round((n / total) * 100) : 0;
        return (
          <div key={status} className="flex items-center gap-2 text-xs">
            <span className="w-20 shrink-0 text-muted">{status}</span>
            <div className="h-3 flex-1 overflow-hidden rounded bg-border">
              <div
                className="h-full rounded"
                style={{ width: `${pct}%`, backgroundColor: statusVar(status) }}
              />
            </div>
            <span className="w-16 shrink-0 text-right text-text">
              {n} ({pct}%)
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** Throughput: job hoàn tất theo ngày (SVG cột). */
function ThroughputChart({ points }: { points: ThroughputPoint[] }) {
  const W = 560;
  const H = 140;
  const pad = { top: 10, bottom: 22, left: 4, right: 4 };
  const max = Math.max(1, ...points.map((p) => p.count));
  const n = points.length;
  const bw = (W - pad.left - pad.right) / n;
  const chartH = H - pad.top - pad.bottom;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Throughput theo ngày">
      <line
        x1={pad.left} y1={H - pad.bottom} x2={W - pad.right} y2={H - pad.bottom}
        stroke="var(--border)" strokeWidth={1}
      />
      {points.map((p, i) => {
        const h = (p.count / max) * chartH;
        const x = pad.left + i * bw;
        const y = H - pad.bottom - h;
        const showLabel = i === 0 || i === n - 1 || i === Math.floor(n / 2);
        return (
          <g key={p.date}>
            <rect
              x={x + bw * 0.15} y={y} width={bw * 0.7} height={Math.max(h, p.count > 0 ? 2 : 0)}
              rx={2} fill="var(--primary)"
            >
              <title>{`${p.date}: ${p.count} job`}</title>
            </rect>
            {p.count > 0 && (
              <text x={x + bw / 2} y={y - 3} textAnchor="middle" fontSize={9} fill="var(--text-muted)">
                {p.count}
              </text>
            )}
            {showLabel && (
              <text
                x={x + bw / 2} y={H - 7} textAnchor="middle" fontSize={9} fill="var(--text-muted)"
              >
                {p.date.slice(5)}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

/** Thời gian trung bình + số lần chạy theo adapter (bảng + thanh). */
function AdapterTable({ adapters }: { adapters: AdapterStat[] }) {
  if (adapters.length === 0) {
    return <p className="text-sm text-muted">Chưa có step nào chạy qua adapter.</p>;
  }
  const maxAvg = Math.max(1, ...adapters.map((a) => a.avg_seconds));
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-muted">
          <tr className="border-b border-border">
            <th className="py-2 pr-3">Adapter</th>
            <th className="py-2 pr-3">Số lần</th>
            <th className="py-2 pr-3">Lỗi</th>
            <th className="py-2 pr-3 w-1/2">Thời gian TB</th>
          </tr>
        </thead>
        <tbody>
          {adapters.map((a) => {
            const pct = Math.round((a.avg_seconds / maxAvg) * 100);
            const failRate = a.count ? Math.round((a.failed / a.count) * 100) : 0;
            return (
              <tr key={a.adapter} className="border-b border-border/50">
                <td className="py-1.5 pr-3 font-mono text-xs text-text">{a.adapter}</td>
                <td className="py-1.5 pr-3 text-muted">{a.count}</td>
                <td className={`py-1.5 pr-3 ${a.failed ? "text-danger" : "text-muted"}`}>
                  {a.failed}
                  {a.failed ? ` (${failRate}%)` : ""}
                </td>
                <td className="py-1.5 pr-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 flex-1 overflow-hidden rounded bg-border">
                      <div
                        className="h-full rounded"
                        style={{ width: `${pct}%`, backgroundColor: "var(--info)" }}
                      />
                    </div>
                    <span className="w-14 shrink-0 text-right text-xs text-muted">
                      {fmtSeconds(a.avg_seconds)}
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Body({ data }: { data: Stats }) {
  const failPct = (data.fail_rate * 100).toFixed(1);
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Tổng job" value={String(data.jobs_total)} />
        <Kpi label="Hoàn tất" value={String(data.completed_total)} accent="var(--success)" />
        <Kpi
          label="Tỉ lệ lỗi"
          value={`${failPct}%`}
          accent={data.fail_rate > 0 ? "var(--danger)" : undefined}
        />
        <Kpi label="Tổng step" value={String(data.steps_total)} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-semibold text-text">Job theo trạng thái</h2>
          <StatusBars byStatus={data.jobs_by_status} total={data.jobs_total} />
        </div>
        <div>
          <h2 className="mb-3 text-sm font-semibold text-text">Step theo trạng thái</h2>
          <StatusBars byStatus={data.steps_by_status} total={data.steps_total} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">
          Throughput — job hoàn tất / ngày ({data.throughput.length} ngày gần nhất)
        </h2>
        <ThroughputChart points={data.throughput} />
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">Hiệu năng theo adapter</h2>
        <AdapterTable adapters={data.adapters} />
      </div>

      <p className="text-right text-xs text-muted">Cập nhật: {fmtDate(data.generated_at)}</p>
    </div>
  );
}

export function Statistics() {
  const stats = useStats();
  const wsConnected = useUiStore((s) => s.wsConnected);

  return (
    <SectionPanel
      title="Statistics"
      description="Thống kê từ data thật — job/step theo trạng thái, throughput, tỉ lệ lỗi, thời gian adapter (SPEC 02 §7)."
      spec="SPEC 02 §7"
    >
      <div className="mb-3 flex items-center gap-2">
        <span className={`text-xs ${wsConnected ? "text-success" : "text-muted"}`}>
          {wsConnected ? "● live" : "○ offline"}
        </span>
        <button
          onClick={() => stats.refetch()}
          className="ml-auto rounded border border-border px-3 py-1 text-xs text-text hover:bg-border"
        >
          ↻ Làm mới
        </button>
      </div>

      {stats.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {stats.isError && (
        <p className="text-sm text-danger">Lỗi: {(stats.error as ApiError)?.message}</p>
      )}
      {stats.data && <Body data={stats.data} />}
    </SectionPanel>
  );
}
