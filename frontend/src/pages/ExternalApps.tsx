import { SectionPanel } from "../components/SectionPanel";

export function ExternalApps() {
  return (
    <SectionPanel
      title="External Applications"
      description="Các app ngoài điều khiển qua Plugin Adapter (SPEC 06)."
      spec="SPEC 06, 08"
    >
      <p className="text-sm text-muted">
        Chrome, Edge, FFmpeg, Google Sheets, Explorer, yt-dlp (Bulk Video Studio &amp; OBS
        hoãn). Quản lý ở Phase Plugin System &amp; Integration.
      </p>
    </SectionPanel>
  );
}
