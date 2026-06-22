import { SectionPanel } from "../components/SectionPanel";

export function Statistics() {
  return (
    <SectionPanel
      title="Statistics"
      description="Thống kê throughput, tỉ lệ lỗi, thời gian adapter (SPEC 02 §7)."
      spec="SPEC 02 §7"
    >
      <p className="text-sm text-muted">
        Biểu đồ số job/giờ và hiệu năng. Triển khai ở Phase Integration.
      </p>
    </SectionPanel>
  );
}
