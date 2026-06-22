import type { Agent } from "../types/api";
import { fmtDate, statusStyle } from "../lib/format";

export function AgentCard({ agent }: { agent: Agent }) {
  const s = statusStyle(agent.status);
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <div className="font-semibold text-text">{agent.id}</div>
        <span className={`text-sm ${s.color}`}>
          {s.icon} {s.label}
        </span>
      </div>
      <div className="mt-1 text-xs text-muted">
        v{agent.version || "?"} · {agent.os || "?"} · capacity {agent.capacity}
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {agent.capabilities.map((c) => (
          <span key={c} className="rounded bg-border px-2 py-0.5 text-xs text-text">
            {c}
          </span>
        ))}
      </div>
      <div className="mt-2 text-xs text-muted">Heartbeat: {fmtDate(agent.last_heartbeat)}</div>
    </div>
  );
}
