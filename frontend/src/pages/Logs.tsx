import { SectionPanel } from "../components/SectionPanel";

export function Logs() {
  return (
    <SectionPanel
      title="Logs"
      description="Nhật ký hệ thống có trace_id (SPEC 04 §7)."
      spec="SPEC 04 §7, 11 §6"
    >
      <p className="text-sm text-muted">
        Xem log theo job/step, lọc theo trace_id. Nối API/WS ở Phase Integration.
      </p>
    </SectionPanel>
  );
}
