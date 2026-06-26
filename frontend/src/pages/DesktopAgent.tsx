import { ApiError } from "../api/client";
import { useAgents } from "../api/hooks";
import { AgentCard } from "../components/AgentCard";
import { SectionPanel } from "../components/SectionPanel";

export function DesktopAgent() {
  const { data, isLoading, isError, error } = useAgents();

  return (
    <SectionPanel
      title="Desktop Agent"
      help="desktop-agent"
      description="Trạng thái agent, capability, nhịp tim (heartbeat) (SPEC 05, 09 §4)."
      spec="SPEC 05, 09 §4"
    >
      {isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {isError && <p className="text-sm text-danger">Lỗi: {(error as ApiError)?.message}</p>}
      {data && data.length === 0 && (
        <p className="text-sm text-muted">
          Chưa có agent kết nối. Chạy Desktop Agent (phase Desktop Agent) để đăng ký qua
          <code> /ws/agent</code>.
        </p>
      )}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {data?.map((a) => (
          <AgentCard key={a.id} agent={a} />
        ))}
      </div>
    </SectionPanel>
  );
}
