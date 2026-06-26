import { useState } from "react";

import { useAgents, useInfo } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { fmtDate } from "../lib/format";
import { useUiStore } from "../store/ui";
import type { ActivityCategory } from "../store/ui";

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-text">{value}</div>
    </div>
  );
}

const FILTERS: { key: ActivityCategory | "all"; label: string }[] = [
  { key: "all", label: "Tất cả" },
  { key: "job", label: "Job" },
  { key: "plugin.runtime", label: "Plugin runtime" },
  { key: "plugin.lifecycle", label: "Plugin lifecycle" },
  { key: "fs", label: "FS" },
  { key: "agent", label: "Agent" },
];

const CAT_COLOR: Record<ActivityCategory, string> = {
  job: "text-info",
  "plugin.runtime": "text-primary",
  "plugin.lifecycle": "text-warning",
  fs: "text-success",
  agent: "text-muted",
};

export function Dashboard() {
  const info = useInfo();
  const agents = useAgents();
  const activities = useUiStore((s) => s.activities);
  const [filter, setFilter] = useState<ActivityCategory | "all">("all");

  const online = agents.data?.filter((a) => a.status === "online").length ?? 0;
  const shown = activities.filter((a) => filter === "all" || a.category === filter);

  return (
    <SectionPanel
      title="Bảng điều khiển"
      help="dashboard"
      description="Tổng quan hệ thống + hoạt động realtime."
      spec="SPEC 12 §5, 09 §4.1"
    >
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Backend" value={info.isError ? "Mất kết nối" : info.data ? "Hoạt động" : "…"} />
        <Kpi label="Phiên bản" value={info.data?.version ?? "—"} />
        <Kpi label="Môi trường" value={info.data?.env ?? "—"} />
        <Kpi label="Agent đang kết nối" value={String(online)} />
      </div>

      <div className="mt-6">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-text">Hoạt động realtime</span>
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`rounded px-2 py-0.5 text-xs ${
                filter === f.key ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="max-h-80 overflow-auto rounded-lg border border-border bg-bg">
          {shown.length === 0 ? (
            <p className="p-3 text-sm text-muted">
              Chưa có hoạt động. Sự kiện job/progress, plugin runtime/lifecycle, fs.event, agent sẽ
              hiện ở đây theo thời gian thực.
            </p>
          ) : (
            <ul className="divide-y divide-border/60">
              {shown.map((a) => (
                <li key={a.id} className="flex items-center gap-3 px-3 py-1.5 text-sm">
                  <span className={`w-28 shrink-0 text-xs ${CAT_COLOR[a.category]}`}>
                    {a.category}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-text">{a.text}</span>
                  <span className="shrink-0 text-xs text-muted">
                    {fmtDate(new Date(a.ts).toISOString()).split(" ")[1] ?? ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </SectionPanel>
  );
}
