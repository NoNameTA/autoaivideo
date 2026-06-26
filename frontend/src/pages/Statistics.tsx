import { useState } from "react";

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

function fmtBytes(b: number): string {
  if (b <= 0) return "0 B";
  const u = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(b) / Math.log(1024)), u.length - 1);
  return `${(b / 1024 ** i).toFixed(1)} ${u[i]}`;
}

function fmtSpeed(bps: number): string {
  return bps > 0 ? `${fmtBytes(bps)}/s` : "—";
}

const AUTO_OPTIONS: { label: string; ms: number }[] = [
  { label: "Tắt", ms: 0 },
  { label: "30 giây", ms: 30_000 },
  { label: "1 phút", ms: 60_000 },
  { label: "5 phút", ms: 300_000 },
];

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

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">Video Sources</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <Kpi label="Nguồn" value={String(data.video.sources_total)} />
          <Kpi label="Tổng video" value={String(data.video.items_total)} />
          <Kpi
            label="Tải xong"
            value={String(data.video.items_by_status.done ?? 0)}
            accent="var(--success)"
          />
          <Kpi
            label="Lỗi"
            value={String(data.video.items_by_status.failed ?? 0)}
            accent={data.video.items_by_status.failed ? "var(--danger)" : undefined}
          />
          <Kpi label="Tổng dung lượng" value={fmtBytes(data.video.total_asset_bytes)} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">Download (yt-dlp / media.download)</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <Kpi label="Tổng lượt tải" value={String(data.download.downloads_total)} />
          <Kpi
            label="Thành công"
            value={String(data.download.downloads_success)}
            accent="var(--success)"
          />
          <Kpi
            label="Lỗi"
            value={String(data.download.downloads_failed)}
            accent={data.download.downloads_failed ? "var(--danger)" : undefined}
          />
          <Kpi label="Dung lượng tải" value={fmtBytes(data.download.total_bytes)} />
          <Kpi label="Tốc độ TB" value={fmtSpeed(data.download.avg_speed_bps)} />
          <Kpi label="Tổng thời gian tải" value={fmtSeconds(data.download.download_seconds)} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">
          Chỉnh sửa &amp; Export (ffmpeg / BVS — lưu trên máy, KHÔNG upload)
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <Kpi label="Tổng lượt chỉnh" value={String(data.edit.edits_total)} />
          <Kpi
            label="Thành công"
            value={String(data.edit.edits_success)}
            accent="var(--success)"
          />
          <Kpi
            label="Lỗi"
            value={String(data.edit.edits_failed)}
            accent={data.edit.edits_failed ? "var(--danger)" : undefined}
          />
          <Kpi label="Đã Export" value={String(data.edit.exported_total)} accent="var(--info)" />
          <Kpi label="Dung lượng xuất" value={fmtBytes(data.edit.export_bytes)} />
          <Kpi label="Thời gian TB" value={fmtSeconds(data.edit.avg_edit_seconds)} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">
          Media Check (ffprobe sau Download — phân loại video thật / audio / hỏng)
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <Kpi label="🎥 Tổng Video" value={String(data.media.video)} accent="var(--success)" />
          <Kpi
            label="🎵 Audio bị bỏ qua"
            value={String(data.media.audio_only)}
            accent={data.media.audio_only ? "var(--warning)" : undefined}
          />
          <Kpi
            label="❌ Invalid"
            value={String(data.media.invalid)}
            accent={data.media.invalid ? "var(--danger)" : undefined}
          />
          <Kpi label="Chưa kiểm" value={String(data.media.unchecked)} />
          <Kpi label="Video đã chỉnh sửa" value={String(data.edit.exported_total)} accent="var(--info)" />
          <Kpi label="Tỷ lệ Video hợp lệ" value={`${Math.round(data.media.valid_ratio * 100)}%`} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text">Cookie Manager</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <Kpi label="Cấu hình" value={String(data.cookies.configured)} />
          <Kpi label="Cookies Loaded" value={String(data.cookies.loaded)} accent="var(--info)" />
          <Kpi label="Cookies Valid" value={String(data.cookies.valid)} accent="var(--success)" />
          <Kpi
            label="Cookies Expired"
            value={String(data.cookies.expired)}
            accent={data.cookies.expired ? "var(--danger)" : undefined}
          />
          <Kpi label="Tải DÙNG cookie" value={String(data.cookies.downloads_with_cookie)} />
          <Kpi label="Tải KHÔNG cookie" value={String(data.cookies.downloads_without_cookie)} />
        </div>
        {Object.keys(data.cookies.downloads_by_platform ?? {}).length > 0 && (
          <div className="mt-3">
            <div className="mb-2 text-xs font-semibold text-muted">Video đã tải theo nền tảng</div>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
              {Object.entries(data.cookies.downloads_by_platform).map(([name, n]) => (
                <Kpi key={name} label={`${name} Downloads`} value={String(n)} />
              ))}
            </div>
          </div>
        )}
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
  const [autoMs, setAutoMs] = useState(0);
  const stats = useStats(autoMs);
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
        <div className="ml-auto flex items-center gap-1 text-xs text-muted">
          <span>Auto</span>
          <select
            className="rounded border border-border bg-bg px-2 py-1 text-text"
            value={autoMs}
            onChange={(e) => setAutoMs(Number(e.target.value))}
          >
            {AUTO_OPTIONS.map((o) => (
              <option key={o.ms} value={o.ms}>{o.label}</option>
            ))}
          </select>
          <button
            onClick={() => stats.refetch()}
            className="rounded border border-border px-3 py-1 text-text hover:bg-border"
          >
            ↻ Làm mới
          </button>
        </div>
      </div>

      {stats.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {stats.isError && (
        <p className="text-sm text-danger">Lỗi: {(stats.error as ApiError)?.message}</p>
      )}
      {stats.data && <Body data={stats.data} />}
    </SectionPanel>
  );
}
