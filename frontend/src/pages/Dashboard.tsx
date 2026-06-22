import { useAgents, useInfo } from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-text">{value}</div>
    </div>
  );
}

export function Dashboard() {
  const info = useInfo();
  const agents = useAgents();

  const online = agents.data?.filter((a) => a.status === "online").length ?? 0;

  return (
    <SectionPanel
      title="Dashboard"
      description="Tổng quan hệ thống và kết nối backend."
      spec="SPEC 12 §5"
    >
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Kpi label="Backend" value={info.isError ? "Offline" : info.data ? "Online" : "…"} />
        <Kpi label="Phiên bản" value={info.data?.version ?? "—"} />
        <Kpi label="Môi trường" value={info.data?.env ?? "—"} />
        <Kpi label="Agent online" value={String(online)} />
      </div>
      <p className="mt-4 text-sm text-muted">
        KPI throughput / tỉ lệ lỗi / danh sách job đang chạy được bổ sung ở phase Workflow &amp;
        Queue (cần execution engine).
      </p>
    </SectionPanel>
  );
}
