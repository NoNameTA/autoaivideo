import { SectionPanel } from "../components/SectionPanel";

export function Queue() {
  return (
    <SectionPanel
      title="Queue"
      description="Hàng đợi tác vụ bền vững (SPEC 04 §4)."
      spec="SPEC 04 §4, 10"
    >
      <p className="text-sm text-muted">
        Hiển thị job_queue, ưu tiên, retry. Nối realtime ở Phase Workflow &amp; Queue.
      </p>
    </SectionPanel>
  );
}
