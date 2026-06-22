// WebSocket client với auto-reconnect + backoff (SPEC 09 §2, §7).

export interface WsMessage {
  v: number;
  type: string;
  id?: string;
  ts?: string;
  trace_id?: string | null;
  data?: Record<string, unknown>;
}

type Listener = (msg: WsMessage) => void;

export class WsClient {
  private ws?: WebSocket;
  private listeners = new Set<Listener>();
  private pending: string[] = [];
  private backoff = 1000;
  private closed = false;

  constructor(
    private getUrl: () => string,
    private onStatus: (connected: boolean) => void,
  ) {}

  connect(): void {
    this.closed = false;
    const ws = new WebSocket(this.getUrl());
    this.ws = ws;

    ws.onopen = () => {
      this.backoff = 1000;
      this.onStatus(true);
      this.pending.forEach((p) => ws.send(p));
      this.pending = [];
    };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as WsMessage;
        this.listeners.forEach((l) => l(msg));
      } catch {
        // bỏ qua message sai định dạng
      }
    };
    ws.onclose = () => {
      this.onStatus(false);
      if (this.closed) return;
      setTimeout(() => this.connect(), this.backoff);
      this.backoff = Math.min(this.backoff * 2, 30_000);
    };
    ws.onerror = () => ws.close();
  }

  private rawSend(payload: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(payload);
    } else {
      this.pending.push(payload);
    }
  }

  send(type: string, data?: unknown): void {
    this.rawSend(JSON.stringify({ v: 1, type, data }));
  }

  subscribe(scope: string, id: string): void {
    this.send("subscribe", { scope, id });
  }

  unsubscribe(scope: string, id: string): void {
    this.send("unsubscribe", { scope, id });
  }

  on(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  close(): void {
    this.closed = true;
    this.ws?.close();
  }
}
