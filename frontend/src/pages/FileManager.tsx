import { SectionPanel } from "../components/SectionPanel";

export function FileManager() {
  return (
    <SectionPanel
      title="File Manager"
      description="Duyệt asset trong Allowed Folders qua Backend → Agent (SPEC 07)."
      spec="SPEC 07, 11 §5"
    >
      <p className="text-sm text-muted">
        Scan/Read/Copy/Move/Rename/Delete/Preview/Watch chỉ trên thư mục được cấp quyền.
        Triển khai ở Phase File Manager. Website không truy cập file trực tiếp.
      </p>
    </SectionPanel>
  );
}
