import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import {
  useAddVideoLinks,
  useConnections,
  useCreateVideoSource,
  useDeleteVideoItem,
  useDeleteVideoSource,
  useImportVideoSheet,
  useReadVideoSheet,
  useRunVideoSource,
  useTestConnection,
  useUpdateVideoSource,
  useVideoItems,
  useVideoSources,
} from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { useUiStore } from "../store/ui";
import type { SheetPreviewRow, VideoSource, VideoSourceItem } from "../types/api";

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-sm text-text";
const STATUS_COLOR: Record<string, string> = {
  pending: "text-muted",
  processing: "text-info",
  done: "text-success",
  failed: "text-danger",
};
const FILTERS = ["", "pending", "processing", "done", "failed"];

export function VideoSources() {
  const sources = useVideoSources();
  const createSrc = useCreateVideoSource();
  const delSrc = useDeleteVideoSource();
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("direct_url");
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const selectedSource = sources.data?.find((s) => s.id === selectedId);

  const addSource = () => {
    if (!newName.trim()) return;
    createSrc.mutate(
      { name: newName.trim(), source_type: newType },
      {
        onSuccess: (s) => {
          setNewName("");
          setSelectedId(s.id);
          push("success", "Đã tạo nguồn");
        },
        onError: onErr,
      },
    );
  };

  return (
    <SectionPanel
      title="Video Sources"
      description="Nguồn video đầu vào — Direct URL (V1). Website tạo Job, Desktop Agent tải bằng yt-dlp (SPEC 02 §4.1)."
      spec="SPEC 02 §4.1, 03 §3, 10"
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input
          className="w-56 rounded border border-border bg-bg px-3 py-1.5 text-sm text-text"
          placeholder="Tên nguồn mới…"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSource()}
        />
        <select
          className="rounded border border-border bg-bg px-2 py-1.5 text-sm text-text"
          value={newType}
          onChange={(e) => setNewType(e.target.value)}
        >
          <option value="direct_url">Direct URL</option>
          <option value="google_sheets">Google Sheets</option>
        </select>
        <button
          onClick={addSource}
          disabled={createSrc.isPending}
          className="rounded bg-primary px-4 py-1.5 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
        >
          + Tạo nguồn
        </button>
      </div>

      {sources.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {sources.data && sources.data.length === 0 && (
        <p className="text-sm text-muted">Chưa có nguồn nào. Tạo nguồn để bắt đầu nhập link.</p>
      )}

      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        {sources.data?.map((s) => (
          <button
            key={s.id}
            onClick={() => setSelectedId(s.id === selectedId ? undefined : s.id)}
            className={`rounded-lg border p-3 text-left ${
              s.id === selectedId ? "border-primary bg-surface" : "border-border bg-bg hover:bg-surface"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text">{s.name}</span>
              <span className="text-xs text-muted">{s.source_type}</span>
            </div>
            <div className="mt-1 text-xs text-muted">
              {s.item_count} video · {s.status}
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                delSrc.mutate(s.id, {
                  onSuccess: () => {
                    if (selectedId === s.id) setSelectedId(undefined);
                    push("success", "Đã xoá nguồn");
                  },
                  onError: onErr,
                });
              }}
              className="mt-2 inline-block cursor-pointer text-xs text-danger hover:underline"
            >
              Xoá
            </span>
          </button>
        ))}
      </div>

      {selectedSource && <SourceDetail key={selectedSource.id} source={selectedSource} />}
    </SectionPanel>
  );
}

function SourceDetail({ source }: { source: VideoSource }) {
  const sourceId = source.id;
  const items = useVideoItems(sourceId);
  const addLinks = useAddVideoLinks(sourceId);
  const delItem = useDeleteVideoItem(sourceId);
  const run = useRunVideoSource(sourceId);
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const [text, setText] = useState("");
  const [filter, setFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const fileRef = useRef<HTMLInputElement>(null);

  const rows = useMemo(() => {
    const data = items.data ?? [];
    return data.filter(
      (it) =>
        (!filter || it.status === filter) &&
        (!search ||
          it.url.toLowerCase().includes(search.toLowerCase()) ||
          (it.title ?? "").toLowerCase().includes(search.toLowerCase())),
    );
  }, [items.data, filter, search]);

  const submitLinks = () => {
    if (!text.trim()) return;
    addLinks.mutate(
      { text },
      { onSuccess: () => { setText(""); push("success", "Đã thêm link"); }, onError: onErr },
    );
  };

  const importFile = async (file: File) => {
    const content = await file.text();
    addLinks.mutate(
      { text: content },
      { onSuccess: () => push("success", `Đã import ${file.name}`), onError: onErr },
    );
  };

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const allShownSelected = rows.length > 0 && rows.every((r) => selected.has(r.id));
  const toggleAll = () =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (allShownSelected) rows.forEach((r) => next.delete(r.id));
      else rows.forEach((r) => next.add(r.id));
      return next;
    });

  const runWorkflow = () => {
    const ids = selected.size > 0 ? Array.from(selected) : undefined;
    run.mutate(
      { item_ids: ids },
      {
        onSuccess: (r) => {
          setSelected(new Set());
          push("success", `Đã tạo ${r.job_count} job download`);
        },
        onError: onErr,
      },
    );
  };

  return (
    <div className="mt-6 rounded-lg border border-border bg-bg p-4">
      {/* Nhập nguồn theo loại */}
      {source.source_type === "google_sheets" ? (
        <SheetConfig source={source} onImported={() => items.refetch()} />
      ) : (
        <div className="mb-4">
          <div className="mb-1 text-sm font-semibold text-text">Nhập link (Direct URL)</div>
          <textarea
            className={`${INPUT} h-24 font-mono`}
            placeholder="Dán nhiều dòng. Hỗ trợ 'Tên, https://...' hoặc chỉ link. (txt/CSV cũng được)"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button
              onClick={submitLinks}
              disabled={addLinks.isPending}
              className="rounded bg-primary px-3 py-1 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
            >
              Add Link
            </button>
            <button
              onClick={() => fileRef.current?.click()}
              className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border"
            >
              Import txt / CSV
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importFile(f);
                e.target.value = "";
              }}
            />
          </div>
        </div>
      )}

      {/* Hành động chung (cả Direct URL & Google Sheets) */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <button
          onClick={() => items.refetch()}
          className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border"
        >
          ↻ Refresh
        </button>
        <button
          onClick={runWorkflow}
          disabled={run.isPending || (items.data?.length ?? 0) === 0}
          className="ml-auto rounded bg-success px-4 py-1 text-sm text-white hover:opacity-90 disabled:opacity-50"
        >
          ▶ Run Workflow{selected.size > 0 ? ` (${selected.size})` : " (tất cả)"}
        </button>
      </div>

      {/* Bộ lọc + tìm kiếm */}
      <div className="mb-2 flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f || "all"}
            onClick={() => setFilter(f)}
            className={`rounded px-2 py-0.5 text-xs ${
              filter === f ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
            }`}
          >
            {f || "tất cả"}
          </button>
        ))}
        <input
          className="ml-auto w-56 rounded border border-border bg-bg px-3 py-1 text-sm text-text"
          placeholder="Tìm link / tên…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Preview */}
      {rows.length === 0 ? (
        <p className="text-sm text-muted">Chưa có video khớp. Nhập link ở trên.</p>
      ) : (
        <div className="max-h-[55vh] overflow-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-bg text-left text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-2">
                  <input type="checkbox" checked={allShownSelected} onChange={toggleAll} />
                </th>
                <th className="py-2 pr-3">STT</th>
                <th className="py-2 pr-3">Tên</th>
                <th className="py-2 pr-3">Link</th>
                <th className="py-2 pr-3">Trạng thái</th>
                <th className="py-2 pr-3">Job</th>
                <th className="py-2 pr-3"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((it: VideoSourceItem) => (
                <tr key={it.id} className="border-b border-border/50">
                  <td className="py-1.5 pr-2">
                    <input
                      type="checkbox"
                      checked={selected.has(it.id)}
                      onChange={() => toggle(it.id)}
                    />
                  </td>
                  <td className="py-1.5 pr-3 text-muted">{it.seq + 1}</td>
                  <td className="py-1.5 pr-3 text-text">{it.title || "—"}</td>
                  <td className="py-1.5 pr-3 max-w-xs truncate font-mono text-xs text-muted" title={it.url}>
                    {it.url}
                  </td>
                  <td className={`py-1.5 pr-3 text-xs ${STATUS_COLOR[it.status] ?? "text-muted"}`}>
                    {it.status}
                  </td>
                  <td className="py-1.5 pr-3 text-xs">
                    {it.job_id ? (
                      <Link to={`/jobs/${it.job_id}`} className="font-mono text-primary hover:underline">
                        {it.job_id.slice(0, 10)}…
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-1.5 pr-3">
                    <button
                      onClick={() =>
                        delItem.mutate(it.id, {
                          onSuccess: () => push("success", "Đã xoá"),
                          onError: onErr,
                        })
                      }
                      className="text-xs text-danger hover:underline"
                    >
                      Xoá
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SheetConfig({ source, onImported }: { source: VideoSource; onImported: () => void }) {
  const connections = useConnections();
  const update = useUpdateVideoSource(source.id);
  const testConn = useTestConnection();
  const readSheet = useReadVideoSheet(source.id);
  const importSheet = useImportVideoSheet(source.id);
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const cfg = source.config as Record<string, string>;
  const [connId, setConnId] = useState(cfg.connection_id ?? "");
  const [spreadsheetId, setSpreadsheetId] = useState(cfg.spreadsheet_id ?? "");
  const [worksheet, setWorksheet] = useState(cfg.worksheet ?? "");
  const [urlColumn, setUrlColumn] = useState(cfg.url_column ?? "VideoURL");
  const [titleColumn, setTitleColumn] = useState(cfg.title_column ?? "");
  const [preview, setPreview] = useState<SheetPreviewRow[] | null>(null);

  const gsConns = (connections.data ?? []).filter((c) => c.provider === "google_sheets");

  const saveConfig = () =>
    update.mutateAsync({
      config: {
        connection_id: connId,
        spreadsheet_id: spreadsheetId.trim(),
        worksheet: worksheet.trim(),
        url_column: urlColumn.trim(),
        title_column: titleColumn.trim() || undefined,
      },
    });

  const onTest = () => {
    if (!connId) return push("error", "Chọn Connection trước");
    testConn.mutate(connId, {
      onSuccess: (r) => push(r.ok ? "success" : "error", r.message),
      onError: onErr,
    });
  };

  const onRead = async () => {
    try {
      await saveConfig();
      const rows = await readSheet.mutateAsync();
      setPreview(rows);
      push("success", `Đọc Sheet: ${rows.length} video`);
    } catch (e) {
      onErr(e);
    }
  };

  const onImport = async () => {
    try {
      await saveConfig();
      const r = await importSheet.mutateAsync();
      setPreview(null);
      onImported();
      push("success", `Đã import ${r.item_count} video`);
    } catch (e) {
      onErr(e);
    }
  };

  return (
    <div className="mb-4">
      <div className="mb-2 text-sm font-semibold text-text">
        Google Sheets (nguồn link — Backend đọc, Agent không tham gia preview)
      </div>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        <select className={INPUT} value={connId} onChange={(e) => setConnId(e.target.value)}>
          <option value="">— Chọn Connection (Google Sheets) —</option>
          {gsConns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.display_name} {c.health_status === "connected" ? "●" : ""}
            </option>
          ))}
        </select>
        <input className={INPUT} value={spreadsheetId} onChange={(e) => setSpreadsheetId(e.target.value)}
          placeholder="Spreadsheet ID" />
        <input className={INPUT} value={worksheet} onChange={(e) => setWorksheet(e.target.value)}
          placeholder="Worksheet (trống = sheet đầu)" />
        <input className={INPUT} value={urlColumn} onChange={(e) => setUrlColumn(e.target.value)}
          placeholder="Cột chứa Link Video (vd VideoURL)" />
        <input className={INPUT} value={titleColumn} onChange={(e) => setTitleColumn(e.target.value)}
          placeholder="Cột Tên (tuỳ chọn)" />
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button onClick={onTest} disabled={testConn.isPending}
          className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border disabled:opacity-50">
          Test Connection
        </button>
        <button onClick={onRead} disabled={readSheet.isPending}
          className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border disabled:opacity-50">
          {readSheet.isPending ? "Đang đọc…" : "Read Sheet (Preview)"}
        </button>
        <button onClick={onImport} disabled={importSheet.isPending}
          className="rounded bg-primary px-3 py-1 text-sm text-white hover:bg-primary-hover disabled:opacity-50">
          {importSheet.isPending ? "Đang import…" : "Import"}
        </button>
        {noConnHint(gsConns.length)}
      </div>

      {preview && (
        <div className="mt-3 max-h-60 overflow-auto rounded border border-border">
          <div className="bg-surface px-3 py-1 text-xs text-muted">
            Preview {preview.length} dòng (chưa import):
          </div>
          <table className="w-full text-sm">
            <tbody>
              {preview.map((r) => (
                <tr key={r.seq} className="border-b border-border/50">
                  <td className="py-1 pl-3 pr-2 text-muted">{r.seq + 1}</td>
                  <td className="py-1 pr-3 text-text">{r.title || "—"}</td>
                  <td className="py-1 pr-3 font-mono text-xs text-muted">{r.url}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function noConnHint(n: number) {
  if (n > 0) return null;
  return (
    <span className="text-xs text-warning">
      Chưa có Connection Google Sheets — tạo ở trang External Applications.
    </span>
  );
}
