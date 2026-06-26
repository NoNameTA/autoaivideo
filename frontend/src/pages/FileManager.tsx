import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { endpoints } from "../api/endpoints";
import { Modal } from "../components/Modal";
import { SectionPanel } from "../components/SectionPanel";
import { getWsClient } from "../hooks/useWebSocket";
import { fmtDate } from "../lib/format";
import { useUiStore } from "../store/ui";
import type { FsEntry } from "../types/fs";

function parentOf(path: string): string {
  const stripped = path.replace(/[/\\]+$/, "");
  const cut = stripped.replace(/[/\\][^/\\]*$/, "");
  return cut || stripped;
}

export function FileManager() {
  const qc = useQueryClient();
  const push = useUiStore((s) => s.pushToast);
  const allowed = useQuery({ queryKey: ["allowed"], queryFn: endpoints.listAllowed });

  const [path, setPath] = useState<string | null>(null);
  const [entries, setEntries] = useState<FsEntry[]>([]);
  const [watching, setWatching] = useState(false);
  const [info, setInfo] = useState<{ title: string; body: string } | null>(null);
  const [newFolder, setNewFolder] = useState("");

  const onError = (e: unknown) => push("error", (e as ApiError).message);

  const scan = async (target: string) => {
    try {
      const res = await endpoints.fsScan(target);
      setPath(res.path);
      setEntries(res.entries);
    } catch (e) {
      onError(e);
    }
  };

  // Realtime: re-scan khi có thay đổi trong thư mục đang xem (SPEC 12 §7).
  useEffect(() => {
    const client = getWsClient();
    if (!client || !path) return;
    return client.on((msg) => {
      if (msg.type === "fs.event") {
        push("info", `Thay đổi: ${(msg.data as { type?: string })?.type ?? "?"}`);
        void scan(path);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);

  const addFolder = useMutation({
    mutationFn: () => endpoints.addAllowed(newFolder.trim(), ""),
    onSuccess: () => {
      setNewFolder("");
      qc.invalidateQueries({ queryKey: ["allowed"] });
      push("success", "Đã thêm Allowed Folder");
    },
    onError,
  });

  const act = async (label: string, fn: () => Promise<unknown>) => {
    try {
      await fn();
      push("success", label);
      if (path) await scan(path);
    } catch (e) {
      onError(e);
    }
  };

  return (
    <SectionPanel
      title="Quản lý tệp"
      help="file-manager"
      description="Duyệt tệp trong các thư mục được phép qua Backend → Agent (SPEC 07, 11 §5)."
      spec="SPEC 07"
    >
      <div className="flex gap-4">
        {/* Allowed Folders */}
        <aside className="w-64 shrink-0">
          <div className="mb-2 text-sm font-semibold text-text">Allowed Folders</div>
          <div className="mb-2 flex gap-1">
            <input
              className="w-full rounded border border-border bg-bg px-2 py-1 text-xs text-text"
              placeholder="C:\\đường\\dẫn"
              value={newFolder}
              onChange={(e) => setNewFolder(e.target.value)}
            />
            <button
              onClick={() => newFolder.trim() && addFolder.mutate()}
              className="rounded bg-primary px-2 text-xs text-white hover:bg-primary-hover"
            >
              +
            </button>
          </div>
          <ul className="flex flex-col gap-1">
            {allowed.data?.map((f) => (
              <li key={f.id} className="flex items-center justify-between gap-1">
                <button
                  onClick={() => scan(f.path)}
                  className="truncate text-left text-xs text-primary hover:underline"
                  title={f.path}
                >
                  {f.label || f.path}
                </button>
                <button
                  onClick={() =>
                    act("Đã gỡ Allowed Folder", () => endpoints.removeAllowed(f.id)).then(() =>
                      qc.invalidateQueries({ queryKey: ["allowed"] }),
                    )
                  }
                  className="text-xs text-danger"
                >
                  ✕
                </button>
              </li>
            ))}
            {allowed.data?.length === 0 && (
              <li className="text-xs text-muted">Chưa có. Thêm 1 thư mục để bắt đầu.</li>
            )}
          </ul>
        </aside>

        {/* Browser */}
        <div className="min-w-0 flex-1">
          {path ? (
            <>
              <div className="mb-3 flex items-center gap-2">
                <button
                  onClick={() => scan(parentOf(path))}
                  className="rounded border border-border px-2 py-1 text-xs text-text hover:bg-border"
                >
                  ↑ Lên
                </button>
                <span className="truncate font-mono text-xs text-muted" title={path}>
                  {path}
                </span>
                <button
                  onClick={() =>
                    act(watching ? "Đã tắt watch" : "Đã bật watch", () =>
                      endpoints.fsWatch(path, !watching),
                    ).then(() => setWatching((w) => !w))
                  }
                  className={`ml-auto rounded px-2 py-1 text-xs ${
                    watching ? "bg-success text-black" : "bg-border text-muted"
                  }`}
                >
                  {watching ? "● Watching" : "○ Watch"}
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-muted">
                    <tr className="border-b border-border">
                      <th className="py-1 pr-3">Tên</th>
                      <th className="py-1 pr-3">Kích thước</th>
                      <th className="py-1 pr-3">Sửa đổi</th>
                      <th className="py-1 pr-3">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((e) => (
                      <tr key={e.path} className="border-b border-border/50">
                        <td className="py-1 pr-3">
                          {e.is_dir ? (
                            <button
                              onClick={() => scan(e.path)}
                              className="text-primary hover:underline"
                            >
                              📁 {e.name}
                            </button>
                          ) : (
                            <span className="text-text">📄 {e.name}</span>
                          )}
                        </td>
                        <td className="py-1 pr-3 text-muted">{e.is_dir ? "—" : `${e.size} B`}</td>
                        <td className="py-1 pr-3 text-xs text-muted">
                          {fmtDate(new Date(e.mtime * 1000).toISOString())}
                        </td>
                        <td className="py-1 pr-3">
                          <div className="flex flex-wrap gap-2 text-xs">
                            {!e.is_dir && (
                              <button
                                onClick={async () => {
                                  try {
                                    const r = await endpoints.fsRead(e.path);
                                    setInfo({
                                      title: e.name,
                                      body:
                                        r.encoding === "text"
                                          ? r.content
                                          : `(base64, ${r.size} bytes)`,
                                    });
                                  } catch (err) {
                                    onError(err);
                                  }
                                }}
                                className="text-primary hover:underline"
                              >
                                Xem
                              </button>
                            )}
                            <button
                              onClick={async () => {
                                try {
                                  const m = await endpoints.fsMetadata(e.path);
                                  setInfo({ title: e.name, body: JSON.stringify(m, null, 2) });
                                } catch (err) {
                                  onError(err);
                                }
                              }}
                              className="text-primary hover:underline"
                            >
                              Info
                            </button>
                            <button
                              onClick={() => {
                                const name = window.prompt("Tên mới", e.name);
                                if (name) void act("Đã đổi tên", () => endpoints.fsRename(e.path, name));
                              }}
                              className="text-primary hover:underline"
                            >
                              Đổi tên
                            </button>
                            <button
                              onClick={() => {
                                const dst = window.prompt("Sao chép tới (đường dẫn đích)", e.path);
                                if (dst) void act("Đã sao chép", () => endpoints.fsCopy(e.path, dst));
                              }}
                              className="text-primary hover:underline"
                            >
                              Copy
                            </button>
                            <button
                              onClick={() => {
                                const dst = window.prompt("Di chuyển tới (đường dẫn đích)", e.path);
                                if (dst) void act("Đã di chuyển", () => endpoints.fsMove(e.path, dst));
                              }}
                              className="text-primary hover:underline"
                            >
                              Move
                            </button>
                            <button
                              onClick={() => {
                                if (window.confirm(`Xoá ${e.name}?`))
                                  void act("Đã xoá", () => endpoints.fsDelete(e.path));
                              }}
                              className="text-danger hover:underline"
                            >
                              Xoá
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {entries.length === 0 && (
                      <tr>
                        <td colSpan={4} className="py-3 text-sm text-muted">
                          Thư mục trống.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted">
              Chọn một Allowed Folder bên trái để duyệt. Mọi thao tác đi qua Backend → Agent; web
              không truy cập file trực tiếp.
            </p>
          )}
        </div>
      </div>

      <Modal open={info !== null} title={info?.title ?? ""} onClose={() => setInfo(null)}>
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded bg-bg p-3 text-xs text-text">
          {info?.body}
        </pre>
      </Modal>
    </SectionPanel>
  );
}
