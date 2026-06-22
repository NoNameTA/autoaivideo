import { statusStyle } from "../lib/format";

export function StatusBadge({ status }: { status: string }) {
  const s = statusStyle(status);
  return (
    <span className={`inline-flex items-center gap-1 text-sm ${s.color}`}>
      <span aria-hidden>{s.icon}</span>
      {s.label}
    </span>
  );
}
