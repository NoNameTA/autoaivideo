import { useState } from "react";

import { ApiError } from "../api/client";
import { useExternalApps, useTestExternalApp } from "../api/hooks";
import { CloudConnections } from "../components/CloudConnections";
import { SectionPanel } from "../components/SectionPanel";
import { useUiStore } from "../store/ui";
import type { ConnectionStatus, ExternalApp, ExternalAppTestResult } from "../types/api";

const CONN: Record<string, { color: string; label: string }> = {
  connected: { color: "text-success", label: "● Đã kết nối" },
  no_agent: { color: "text-warning", label: "○ Chưa có agent" },
  disabled: { color: "text-muted", label: "○ Đã tắt" },
};

function ConnBadge({ c }: { c: ConnectionStatus }) {
  const s = CONN[c.status] ?? CONN.disabled;
  return (
    <span className={`text-xs ${s.color}`} title={c.online_agents.join(", ")}>
      {s.label}
      {c.status === "connected" ? ` (${c.online_agents.join(", ")})` : ""}
      {c.status === "connected" && !c.capacity_free ? " · hết slot" : ""}
    </span>
  );
}

export function ExternalApps() {
  const apps = useExternalApps();
  const test = useTestExternalApp();
  const push = useUiStore((s) => s.pushToast);
  const wsConnected = useUiStore((s) => s.wsConnected);
  const [type, setType] = useState("");
  const [results, setResults] = useState<Record<string, ExternalAppTestResult>>({});

  const data = apps.data ?? [];
  const types = Array.from(new Set(data.map((a) => a.type).filter(Boolean))).sort();
  const shown = data.filter((a) => !type || a.type === type);

  const onTest = (app: ExternalApp) => {
    test.mutate(app.name, {
      onSuccess: (r) => {
        setResults((prev) => ({ ...prev, [app.name]: r }));
        push(r.ok ? "success" : "error", `${app.name}: ${r.reason}`);
      },
      onError: (e) => push("error", (e as ApiError).message),
    });
  };

  return (
    <SectionPanel
      title="External Applications"
      description="App ngoài điều khiển qua Adapter — loại tích hợp, trạng thái kết nối, test kết nối (SPEC 06)."
      spec="SPEC 06, 08"
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button
          onClick={() => setType("")}
          className={`rounded px-3 py-1 text-xs ${
            type === "" ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
          }`}
        >
          tất cả
        </button>
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setType(t)}
            className={`rounded px-3 py-1 text-xs ${
              type === t ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
            }`}
          >
            {t}
          </button>
        ))}
        <span className={`ml-auto text-xs ${wsConnected ? "text-success" : "text-muted"}`}>
          {wsConnected ? "● live" : "○ offline"}
        </span>
        <button
          onClick={() => apps.refetch()}
          className="rounded border border-border px-3 py-1 text-xs text-text hover:bg-border"
        >
          ↻
        </button>
      </div>

      {apps.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {apps.isError && (
        <p className="text-sm text-danger">Lỗi: {(apps.error as ApiError)?.message}</p>
      )}
      {apps.data && shown.length === 0 && (
        <p className="text-sm text-muted">
          Chưa có app ngoài nào. Thêm app = thêm plugin adapter (SPEC 06 §7, 08).
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {shown.map((app) => {
          const r = results[app.name];
          return (
            <div key={app.name} className="rounded-lg border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <div className="font-semibold text-text">{app.name}</div>
                <ConnBadge c={app.connection} />
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                <span className="rounded bg-border px-1.5 py-0.5 text-text">{app.type || "?"}</span>
                <span className="font-mono">{app.capability}</span>
                <span>v{app.version || "?"}</span>
                <span className={app.enabled ? "text-success" : "text-muted"}>
                  {app.enabled ? "bật" : "tắt"}
                </span>
                {app.free && <span className="text-success">free</span>}
              </div>
              {(app.license || app.source_url) && (
                <div className="mt-1 text-xs text-muted">
                  {app.license && <span>{app.license}</span>}
                  {app.license && app.source_url && <span> · </span>}
                  {app.source_url && (
                    <a
                      href={app.source_url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="text-primary hover:underline"
                    >
                      nguồn ↗
                    </a>
                  )}
                </div>
              )}

              <div className="mt-3 flex items-center gap-3">
                <button
                  onClick={() => onTest(app)}
                  disabled={test.isPending && test.variables === app.name}
                  className="rounded bg-primary px-3 py-1 text-xs text-white hover:bg-primary-hover disabled:opacity-50"
                >
                  {test.isPending && test.variables === app.name ? "Đang test…" : "Test kết nối"}
                </button>
                {r && (
                  <span className={`text-xs ${r.ok ? "text-success" : "text-danger"}`}>
                    {r.ok ? "✓ " : "✕ "}
                    {r.reason}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <CloudConnections />
    </SectionPanel>
  );
}
