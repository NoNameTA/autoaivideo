// Quản lý vòng đời 1 kết nối WS dashboard + đồng bộ React Query khi có realtime (SPEC 03 §4).
import { useEffect } from "react";

import { WsClient, type WsMessage } from "../api/ws";
import { qk } from "../api/hooks";
import { queryClient } from "../lib/queryClient";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

let activeClient: WsClient | null = null;

function basename(p: unknown): string {
  return typeof p === "string" ? p.split(/[/\\]/).pop() || p : "";
}

/** Phân loại message WS thành mục Activity cho Dashboard (SPEC 09 §4.1). */
function pushActivity(msg: WsMessage): void {
  const d = (msg.data ?? {}) as Record<string, unknown>;
  const add = useUiStore.getState().pushActivity;
  if (msg.type === "activity") {
    const kind = String(d.kind ?? "");
    if (kind.startsWith("plugin.runtime")) {
      add({ category: "plugin.runtime", kind, text: `${kind} · ${d.capability ?? ""}` });
    } else if (kind.startsWith("plugin.lifecycle")) {
      add({ category: "plugin.lifecycle", kind, text: `${kind} · ${d.name ?? ""}` });
    } else if (kind === "job.updated") {
      add({ category: "job", kind, text: `job ${d.status} ${d.progress ?? 0}%` });
    }
  } else if (msg.type === "fs.event") {
    add({ category: "fs", kind: String(d.type ?? "fs"), text: `${d.type}: ${basename(d.path)}` });
  } else if (msg.type === "agent.updated") {
    add({ category: "agent", kind: "agent.updated", text: `${d.agent_id}: ${d.status}` });
  }
}

export function getWsClient(): WsClient | null {
  return activeClient;
}

function wsUrl(token: string): string {
  const base = useSettingsStore.getState().apiBase || window.location.origin;
  return `${base.replace(/^http/, "ws")}/ws?token=${encodeURIComponent(token)}`;
}

/** Gọi 1 lần ở Layout. Tạo/kết nối WS khi có token, tự dọn khi token đổi/unmount. */
export function useWebSocketConnection(): void {
  const token = useSettingsStore((s) => s.token);
  const setWsConnected = useUiStore((s) => s.setWsConnected);

  useEffect(() => {
    if (!token) {
      setWsConnected(false);
      return;
    }
    const client = new WsClient(() => wsUrl(token), setWsConnected);
    activeClient = client;
    const off = client.on((msg) => {
      // Realtime -> làm mới cache liên quan (SPEC 09 §3).
      if (msg.type === "agent.updated") {
        queryClient.invalidateQueries({ queryKey: qk.agents });
        // Kết nối External Apps phụ thuộc agent online (SPEC 06 §7).
        queryClient.invalidateQueries({ queryKey: ["external-apps"] });
      } else if (msg.type.startsWith("batch.") || msg.type.startsWith("job.") || msg.type.startsWith("step.")) {
        queryClient.invalidateQueries({ queryKey: ["batchJobs"] });
        queryClient.invalidateQueries({ queryKey: ["job"] });
        queryClient.invalidateQueries({ queryKey: ["batch"] });
        queryClient.invalidateQueries({ queryKey: ["jobs-all"] });
        queryClient.invalidateQueries({ queryKey: ["stats"] });
        // Trạng thái video item suy từ job -> làm mới realtime (SPEC 02 §4.1).
        queryClient.invalidateQueries({ queryKey: ["video-items"] });
      }
      // Mọi activity/fs.event/agent.updated đều được backend ghi vào audit-log
      // (bảng events) -> làm mới trang Logs realtime (SPEC 04 §7).
      if (
        msg.type === "activity" ||
        msg.type === "fs.event" ||
        msg.type === "agent.updated"
      ) {
        queryClient.invalidateQueries({ queryKey: ["logs"] });
      }
      // Dashboard Activity Stream (SPEC 09 §4.1, 12 §5).
      pushActivity(msg);
    });
    client.connect();

    return () => {
      off();
      client.close();
      activeClient = null;
      setWsConnected(false);
    };
  }, [token, setWsConnected]);
}

/** Subscribe 1 kênh (vd batch) trong khi component sống. */
export function useSubscribe(scope: string, id: string | undefined): void {
  const token = useSettingsStore((s) => s.token);
  useEffect(() => {
    if (!id || !token) return;
    const client = getWsClient();
    client?.subscribe(scope, id);
    return () => client?.unsubscribe(scope, id);
  }, [scope, id, token]);
}
