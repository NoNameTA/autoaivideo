// Map trạng thái -> màu/icon (SPEC 12 §4) + tiện ích định dạng.

export interface StatusStyle {
  color: string;
  icon: string;
  label: string;
}

export const STATUS_STYLE: Record<string, StatusStyle> = {
  queued: { color: "text-muted", icon: "⏳", label: "queued" },
  assigned: { color: "text-info", icon: "▦", label: "assigned" },
  running: { color: "text-info", icon: "▶", label: "running" },
  completed: { color: "text-success", icon: "✓", label: "completed" },
  failed: { color: "text-danger", icon: "✕", label: "failed" },
  retrying: { color: "text-warning", icon: "↻", label: "retrying" },
  cancelled: { color: "text-muted", icon: "⊘", label: "cancelled" },
  created: { color: "text-muted", icon: "•", label: "created" },
  online: { color: "text-success", icon: "●", label: "online" },
  offline: { color: "text-muted", icon: "○", label: "offline" },
  busy: { color: "text-warning", icon: "◐", label: "busy" },
};

export function statusStyle(status: string): StatusStyle {
  return STATUS_STYLE[status] ?? { color: "text-muted", icon: "•", label: status };
}

export function fmtDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}
