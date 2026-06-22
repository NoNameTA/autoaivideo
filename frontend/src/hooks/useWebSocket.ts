// Quản lý vòng đời 1 kết nối WS dashboard + đồng bộ React Query khi có realtime (SPEC 03 §4).
import { useEffect } from "react";

import { WsClient } from "../api/ws";
import { qk } from "../api/hooks";
import { queryClient } from "../lib/queryClient";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

let activeClient: WsClient | null = null;

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
      } else if (msg.type.startsWith("batch.") || msg.type.startsWith("job.") || msg.type.startsWith("step.")) {
        queryClient.invalidateQueries({ queryKey: ["batchJobs"] });
        queryClient.invalidateQueries({ queryKey: ["job"] });
        queryClient.invalidateQueries({ queryKey: ["batch"] });
      }
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
