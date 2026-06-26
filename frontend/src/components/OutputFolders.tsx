import { useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { HelpTip } from "./HelpTip";
import { useFolders, useSaveFolders } from "../api/hooks";
import { useUiStore } from "../store/ui";

const INPUT = "w-full rounded border border-border bg-bg px-2 py-1 text-sm text-text";

/**
 * Output Folders — nơi lưu video TRÊN MÁY (KHÔNG upload, KHÔNG cloud).
 * Desktop Agent đọc các thư mục này qua job inputs (Backend nhúng khi tạo Job).
 */
export function OutputFolders() {
  const folders = useFolders();
  const save = useSaveFolders();
  const push = useUiStore((s) => s.pushToast);

  const [download, setDownload] = useState("");
  const [exportF, setExportF] = useState("");
  const [temp, setTemp] = useState("");

  useEffect(() => {
    if (folders.data) {
      setDownload(folders.data.download_folder);
      setExportF(folders.data.export_folder);
      setTemp(folders.data.temp_folder);
    }
  }, [folders.data]);

  const onSave = () => {
    save.mutate(
      {
        download_folder: download.trim(),
        export_folder: exportF.trim(),
        temp_folder: temp.trim(),
      },
      {
        onSuccess: () => push("success", "Đã lưu Output Folders"),
        onError: (e) => push("error", (e as ApiError).message),
      },
    );
  };

  return (
    <div className="rounded-lg border border-border bg-surface/40 p-4">
      <div className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-text">
        Thư mục lưu video (trên máy)
        <HelpTip id="output-folders" />
      </div>
      <p className="mb-3 text-xs text-muted">
        Video chỉ lưu TRÊN MÁY Windows — KHÔNG upload, KHÔNG cloud. Agent lưu video tải về vào
        Download Folder, video đã chỉnh/Export vào Export Folder. Để trống = giữ mặc định.
      </p>

      <div className="grid gap-3 sm:grid-cols-1">
        <label className="flex flex-col gap-1 text-sm text-muted">
          Download Folder (video tải về)
          <input className={INPUT} value={download} onChange={(e) => setDownload(e.target.value)}
            placeholder="C:\Users\PC\Videos\video gốc" />
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted">
          Export Folder (video đã chỉnh / Export)
          <input className={INPUT} value={exportF} onChange={(e) => setExportF(e.target.value)}
            placeholder="C:\Users\PC\Videos\video da sua" />
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted">
          Temp Folder (tạm)
          <input className={INPUT} value={temp} onChange={(e) => setTemp(e.target.value)}
            placeholder="C:\Users\PC\Videos\temp" />
        </label>
      </div>

      <div className="mt-3">
        <button
          onClick={onSave}
          disabled={save.isPending}
          className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
        >
          💾 Lưu Output Folders
        </button>
      </div>
    </div>
  );
}
