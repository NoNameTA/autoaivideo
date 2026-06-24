import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import {
  useAddVideoLinks,
  useCreateVideoSource,
  useDeleteVideoItem,
  useDeleteVideoSource,
  useRunVideoSource,
  useVideoItems,
  useVideoSources,
} from "../api/hooks";
import { SectionPanel } from "../components/SectionPanel";
import { useUiStore } from "../store/ui";
import type { VideoSourceItem } from "../types/api";

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
  const [selectedId, setSelectedId] = useState<string | undefined>();

  const addSource = () => {
    if (!newName.trim()) return;
    createSrc.mutate(
      { name: newName.trim(), source_type: "direct_url" },
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
          className="w-64 rounded border border-border bg-bg px-3 py-1.5 text-sm text-text"
          placeholder="Tên nguồn mới…"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSource()}
        />
        <button
          onClick={addSource}
          disabled={createSrc.isPending}
          className="rounded bg-primary px-4 py-1.5 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
        >
          + Tạo nguồn (Direct URL)
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

      {selectedId && <SourceDetail key={selectedId} sourceId={selectedId} />}
    </SectionPanel>
  );
}

function SourceDetail({ sourceId }: { sourceId: string }) {
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
      {/* Nhập / import link */}
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
