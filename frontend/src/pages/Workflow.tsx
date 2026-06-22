import { SectionPanel } from "../components/SectionPanel";

export function Workflow() {
  return (
    <SectionPanel
      title="Workflow"
      description="Pipeline/template các bước xử lý (SPEC 02 §4)."
      spec="SPEC 02 §4"
    >
      <p className="text-sm text-muted">
        Chọn template pipeline và theo dõi DAG các Step. Triển khai ở Phase Workflow &amp;
        Queue.
      </p>
    </SectionPanel>
  );
}
