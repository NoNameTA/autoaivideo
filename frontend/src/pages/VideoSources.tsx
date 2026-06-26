import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import {
  useAddVideoLinks,
  useBvsEdit,
  useConnections,
  useCountVideoSheet,
  useCreateVariations,
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
  useVideoSourcesSummary,
} from "../api/hooks";
import { HelpTip } from "../components/HelpTip";
import { SectionPanel } from "../components/SectionPanel";
import { useUiStore } from "../store/ui";
import type {
  SheetReadRequest,
  SheetPreviewRow,
  VideoSource,
  VideoSourceItem,
  VideoSourcesSummary,
} from "../types/api";

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-sm text-text";
const STATUS_COLOR: Record<string, string> = {
  pending: "text-muted",
  processing: "text-info",
  done: "text-success",
  failed: "text-danger",
};
const FILTERS = ["", "pending", "processing", "done", "failed"];

// Media Check (ffprobe sau Download): icon + nhãn + màu.
const MEDIA_META: Record<string, { icon: string; label: string; cls: string }> = {
  video: { icon: "🎥", label: "Video", cls: "text-success" },
  audio_only: { icon: "🎵", label: "Audio Only", cls: "text-warning" },
  invalid: { icon: "❌", label: "Invalid", cls: "text-danger" },
};
// Bộ lọc theo Media Type. "" = tất cả; "unchecked" = chưa kiểm.
const MEDIA_FILTERS: { v: string; label: string }[] = [
  { v: "", label: "Media: tất cả" },
  { v: "video", label: "🎥 Video" },
  { v: "audio_only", label: "🎵 Audio Only" },
  { v: "invalid", label: "❌ Invalid" },
];

// Auto Refresh (incremental qua React Query refetchInterval — không reload trang).
const AUTO_OPTIONS: { label: string; ms: number }[] = [
  { label: "Tắt", ms: 0 },
  { label: "30 giây", ms: 30_000 },
  { label: "1 phút", ms: 60_000 },
  { label: "5 phút", ms: 300_000 },
];

// Bộ lọc Import (Backend lọc theo cột Status của Sheet).
const IMPORT_FILTERS: { value: NonNullable<SheetReadRequest["filter"]>; label: string }[] = [
  { value: "all", label: "Tất cả" },
  { value: "unprocessed", label: "Chưa xử lý" },
  { value: "failed", label: "Lỗi" },
  { value: "not_downloaded", label: "Chưa download" },
];

// Batch Import (số lượng tối đa mỗi lần import).
const BATCH_LIMITS: { value: number; label: string }[] = [
  { value: 0, label: "Toàn bộ" },
  { value: 100, label: "100" },
  { value: 500, label: "500" },
  { value: 1000, label: "1000" },
  { value: 5000, label: "5000" },
];

export function VideoSources() {
  const [autoMs, setAutoMs] = useState(0);
  const sources = useVideoSources(autoMs);
  const summary = useVideoSourcesSummary(autoMs);
  const createSrc = useCreateVideoSource();
  const delSrc = useDeleteVideoSource();
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("direct_url");
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const selectedSource = sources.data?.find((s) => s.id === selectedId);
  const byId = useMemo(
    () => new Map((summary.data?.sources ?? []).map((r) => [r.id, r])),
    [summary.data],
  );

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
      title="Nguồn video"
      help="video-sources"
      description="Nguồn video đầu vào — Direct URL (dán link) hoặc Google Sheets. Website tạo Job, Desktop Agent tải bằng yt-dlp (SPEC 02 §4.1)."
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
        {/* Auto Refresh (incremental, không reload trang) */}
        <div className="ml-auto flex items-center gap-1 text-xs text-muted">
          <span>Tự làm mới</span>
          <select
            className="rounded border border-border bg-bg px-2 py-1 text-text"
            value={autoMs}
            onChange={(e) => setAutoMs(Number(e.target.value))}
          >
            {AUTO_OPTIONS.map((o) => (
              <option key={o.ms} value={o.ms}>{o.label}</option>
            ))}
          </select>
          <button
            onClick={() => {
              sources.refetch();
              summary.refetch();
            }}
            className="rounded border border-border px-2 py-1 text-text hover:bg-border"
          >
            ↻ Làm mới
          </button>
        </div>
      </div>

      <SummaryHeader summary={summary.data} />

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
            <SourceBadges row={byId.get(s.id)} duplicate={s.duplicate_count ?? 0} />
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

      {selectedSource && (
        <SourceDetail key={selectedSource.id} source={selectedSource} autoMs={autoMs} />
      )}
    </SectionPanel>
  );
}

function StatPill({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="rounded border border-border bg-bg px-2 py-1 text-center">
      <div className={`text-base font-semibold ${color ?? "text-text"}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted">{label}</div>
    </div>
  );
}

function SummaryHeader({ summary }: { summary: VideoSourcesSummary | undefined }) {
  if (!summary) return null;
  const t = summary.totals;
  const byType = Object.entries(summary.by_type);
  return (
    <div className="mb-4 rounded-lg border border-border bg-surface p-3">
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-8">
        <StatPill label="Tổng video" value={t.items} />
        <StatPill label="Imported" value={t.items} />
        <StatPill label="Ready" value={t.pending} color="text-muted" />
        <StatPill label="Running" value={t.processing} color="text-info" />
        <StatPill label="Done" value={t.done} color="text-success" />
        <StatPill label="Failed" value={t.failed} color="text-danger" />
        <StatPill label="Duplicate" value={t.duplicate} color="text-warning" />
        <StatPill label="Nguồn" value={t.sources} />
      </div>
      {byType.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted">
          <span className="text-muted">Theo loại:</span>
          {byType.map(([type, v]) => (
            <span key={type} className="rounded bg-border px-2 py-0.5">
              {type}: {v.items} video · {v.sources} nguồn
              {v.duplicate ? ` · dup ${v.duplicate}` : ""}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function SourceBadges({
  row,
  duplicate,
}: {
  row: VideoSourcesSummary["sources"][number] | undefined;
  duplicate: number;
}) {
  if (!row) return null;
  const b = row.by_status;
  const chips: { label: string; n: number; cls: string }[] = [
    { label: "Ready", n: b.pending, cls: "text-muted" },
    { label: "Run", n: b.processing, cls: "text-info" },
    { label: "Done", n: b.done, cls: "text-success" },
    { label: "Fail", n: b.failed, cls: "text-danger" },
    { label: "Dup", n: duplicate, cls: "text-warning" },
  ].filter((c) => c.n > 0);
  if (chips.length === 0) return null;
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {chips.map((c) => (
        <span key={c.label} className={`rounded bg-border px-1.5 py-0.5 text-[10px] ${c.cls}`}>
          {c.label} {c.n}
        </span>
      ))}
    </div>
  );
}

function SourceDetail({ source, autoMs }: { source: VideoSource; autoMs: number }) {
  const sourceId = source.id;
  const items = useVideoItems(sourceId, autoMs);
  const addLinks = useAddVideoLinks(sourceId);
  const delItem = useDeleteVideoItem(sourceId);
  const run = useRunVideoSource(sourceId);
  const variations = useCreateVariations(sourceId);
  const bvsEdit = useBvsEdit(sourceId);
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const [text, setText] = useState("");
  const [filter, setFilter] = useState("");
  const [mediaFilter, setMediaFilter] = useState(""); // lọc theo Media Type (ffprobe)
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  // Tạo biến thể (1 video -> N) — tuỳ chọn.
  const [varCount, setVarCount] = useState(3);
  const [varSpin, setVarSpin] = useState(true);
  const [varRatio, setVarRatio] = useState(true);
  const [varCaption, setVarCaption] = useState(false);
  // Tuỳ chỉnh Bulk Video Studio (logo/intro/outro/nhạc/speed) — map đúng Config của BulkAuto.
  const [bvsOpen, setBvsOpen] = useState(false);
  const [bvsLogo, setBvsLogo] = useState("");
  const [bvsLogoProb, setBvsLogoProb] = useState(0.7);
  const [bvsIntro, setBvsIntro] = useState("");
  const [bvsIntroProb, setBvsIntroProb] = useState(0.4);
  const [bvsOutro, setBvsOutro] = useState("");
  const [bvsOutroProb, setBvsOutroProb] = useState(0.4);
  const [bvsMusic, setBvsMusic] = useState("");
  const [bvsSpeed, setBvsSpeed] = useState("auto");
  const fileRef = useRef<HTMLInputElement>(null);

  const rows = useMemo(() => {
    const data = items.data ?? [];
    return data.filter(
      (it) =>
        (!filter || it.status === filter) &&
        (!mediaFilter ||
          (mediaFilter === "unchecked" ? !it.media_type : it.media_type === mediaFilter)) &&
        (!search ||
          it.url.toLowerCase().includes(search.toLowerCase()) ||
          (it.title ?? "").toLowerCase().includes(search.toLowerCase())),
    );
  }, [items.data, filter, mediaFilter, search]);

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

  const runVariations = () => {
    const targets = (items.data ?? []).filter(
      (it) => selected.has(it.id) && it.status === "done",
    );
    if (targets.length === 0) {
      push("error", "Chọn video ĐÃ TẢI XONG (done) để tạo biến thể");
      return;
    }
    targets.forEach((it) =>
      variations.mutate(
        {
          itemId: it.id,
          count: varCount,
          spin: varSpin,
          ratio: varRatio,
          caption: varCaption,
        },
        {
          onSuccess: (r) => push("success", `🎬 Đã tạo ${r.count} biến thể cho "${it.title || "video"}"`),
          onError: onErr,
        },
      ),
    );
  };

  // Gom tuỳ chỉnh BVS thành bvs_config (chỉ gửi field đã nhập → field trống = giữ mặc định BVS).
  const buildBvsConfig = (): Record<string, unknown> | undefined => {
    const cfg: Record<string, unknown> = {};
    if (bvsLogo.trim()) {
      cfg.logo_folder = bvsLogo.trim();
      cfg.logo_prob = bvsLogoProb;
    }
    if (bvsIntro.trim()) {
      cfg.intro_folder = bvsIntro.trim();
      cfg.intro_prob = bvsIntroProb;
    }
    if (bvsOutro.trim()) {
      cfg.outro_folder = bvsOutro.trim();
      cfg.outro_prob = bvsOutroProb;
    }
    if (bvsMusic.trim()) cfg.music_folder = bvsMusic.trim();
    if (bvsSpeed && bvsSpeed !== "auto") cfg.speed_mode = bvsSpeed;
    return Object.keys(cfg).length ? cfg : undefined;
  };

  const runBvsEdit = () => {
    const targets = (items.data ?? []).filter(
      (it) => selected.has(it.id) && it.status === "done",
    );
    if (targets.length === 0) {
      push("error", "Chọn video ĐÃ TẢI XONG (done) để chỉnh bằng BVS");
      return;
    }
    const bvs_config = buildBvsConfig();
    targets.forEach((it) =>
      bvsEdit.mutate(
        { itemId: it.id, bvs_config },
        {
          onSuccess: () => push("success", `🎞️ Đã gửi "${it.title || "video"}" cho Bulk Video Studio chỉnh`),
          onError: onErr,
        },
      ),
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
              Thêm link
            </button>
            <button
              onClick={() => fileRef.current?.click()}
              className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border"
            >
              Nhập txt / CSV
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
        <HelpTip id="run-workflow" className="ml-auto" />
        <button
          onClick={runWorkflow}
          disabled={run.isPending || (items.data?.length ?? 0) === 0}
          className="rounded bg-success px-4 py-1 text-sm text-white hover:opacity-90 disabled:opacity-50"
        >
          ▶ Chạy quy trình{selected.size > 0 ? ` (${selected.size})` : " (tất cả)"}
        </button>
      </div>

      {/* Tạo biến thể (1 video đã tải -> N bản chỉnh sửa bằng ffmpeg) */}
      <div className="mb-3 flex flex-wrap items-center gap-2 rounded border border-border bg-bg p-2 text-sm">
        <span className="flex items-center gap-1 font-medium text-text">🎬 Biến thể <HelpTip id="variations" /></span>
        <label className="flex items-center gap-1 text-muted">
          Số bản
          <input type="number" min={1} max={50} value={varCount}
            onChange={(e) => setVarCount(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
            className="w-16 rounded border border-border bg-bg px-2 py-1 text-text" />
        </label>
        <label className="flex items-center gap-1 text-muted" title="Đổi tốc độ/lật/zoom/màu để tránh trùng lặp">
          <input type="checkbox" checked={varSpin} onChange={(e) => setVarSpin(e.target.checked)} />
          Spin
        </label>
        <label className="flex items-center gap-1 text-muted" title="Tạo bản 9:16, 1:1, 16:9">
          <input type="checkbox" checked={varRatio} onChange={(e) => setVarRatio(e.target.checked)} />
          Đổi tỉ lệ
        </label>
        <label className="flex items-center gap-1 text-muted" title="Chèn tên video làm caption">
          <input type="checkbox" checked={varCaption} onChange={(e) => setVarCaption(e.target.checked)} />
          Caption
        </label>
        <button onClick={runVariations} disabled={variations.isPending}
          className="ml-auto rounded bg-primary px-3 py-1 text-white hover:bg-primary-hover disabled:opacity-50">
          🎬 Tạo biến thể (video done đã chọn)
        </button>
        <button onClick={runBvsEdit} disabled={bvsEdit.isPending}
          title="Chỉnh bằng bộ công cụ Bulk Video Studio (Agent tự mở BVS)"
          className="rounded border border-border px-3 py-1 text-text hover:bg-border disabled:opacity-50">
          🎞️ Chỉnh bằng BVS
        </button>
        <HelpTip id="bvs-edit" />
        <button onClick={() => setBvsOpen((v) => !v)}
          title="Tuỳ chỉnh logo / intro / outro / nhạc / tốc độ cho BVS"
          className="rounded border border-border px-2 py-1 text-xs text-muted hover:bg-border">
          ⚙️ Tuỳ chỉnh BVS {bvsOpen ? "▲" : "▼"}
        </button>
      </div>

      {/* Form tuỳ chỉnh BVS — map đúng Config BulkAuto (logo/intro/outro/nhạc/speed). Trống = mặc định. */}
      {bvsOpen && (
        <div className="mb-3 grid gap-3 rounded border border-border bg-bg p-3 text-sm sm:grid-cols-2">
          <div className="sm:col-span-2 text-xs text-muted">
            Nhập đường dẫn THƯ MỤC trên máy chạy Agent (chứa file logo/intro/outro/nhạc). Để trống =
            giữ cấu hình mặc định của BVS. Tỉ lệ áp dụng 0–1 (vd 0.7 = 70% video được chèn).
          </div>
          <label className="flex flex-col gap-1 text-muted">
            Thư mục Logo
            <input className={INPUT} placeholder="vd: C:\BVS\logos" value={bvsLogo}
              onChange={(e) => setBvsLogo(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Tỉ lệ chèn Logo
            <input type="number" min={0} max={1} step={0.05} value={bvsLogoProb}
              onChange={(e) => setBvsLogoProb(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
              className={INPUT} disabled={!bvsLogo.trim()} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Thư mục Intro
            <input className={INPUT} placeholder="vd: C:\BVS\intro" value={bvsIntro}
              onChange={(e) => setBvsIntro(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Tỉ lệ chèn Intro
            <input type="number" min={0} max={1} step={0.05} value={bvsIntroProb}
              onChange={(e) => setBvsIntroProb(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
              className={INPUT} disabled={!bvsIntro.trim()} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Thư mục Outro
            <input className={INPUT} placeholder="vd: C:\BVS\outro" value={bvsOutro}
              onChange={(e) => setBvsOutro(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Tỉ lệ chèn Outro
            <input type="number" min={0} max={1} step={0.05} value={bvsOutroProb}
              onChange={(e) => setBvsOutroProb(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
              className={INPUT} disabled={!bvsOutro.trim()} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Thư mục Nhạc nền
            <input className={INPUT} placeholder="vd: C:\BVS\music" value={bvsMusic}
              onChange={(e) => setBvsMusic(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-muted">
            Chế độ tốc độ (speed)
            <select className={INPUT} value={bvsSpeed} onChange={(e) => setBvsSpeed(e.target.value)}>
              <option value="auto">auto (mặc định)</option>
              <option value="marker">marker (theo tên file)</option>
              <option value="heuristic">heuristic (dò cảnh)</option>
              <option value="off">off (giữ nguyên)</option>
            </select>
          </label>
        </div>
      )}

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
        <span className="ml-2 text-border">|</span>
        {MEDIA_FILTERS.map((m) => (
          <button
            key={m.v || "media-all"}
            onClick={() => setMediaFilter(m.v)}
            title="Lọc theo Media Type (ffprobe sau Download)"
            className={`rounded px-2 py-0.5 text-xs ${
              mediaFilter === m.v ? "bg-primary text-white" : "bg-border text-muted hover:text-text"
            }`}
          >
            {m.label}
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
                <th className="py-2 pr-3"><span className="inline-flex items-center gap-1">Media <HelpTip id="media-type" /></span></th>
                <th className="py-2 pr-3"><span className="inline-flex items-center gap-1">Output <HelpTip id="output-path" /></span></th>
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
                    {it.media_type && MEDIA_META[it.media_type] ? (
                      <span className={MEDIA_META[it.media_type].cls}
                        title={`Media Check (ffprobe): ${MEDIA_META[it.media_type].label}`}>
                        {MEDIA_META[it.media_type].icon} {MEDIA_META[it.media_type].label}
                      </span>
                    ) : (
                      <span className="text-muted" title="Chưa kiểm (chưa tải xong / chờ Media Check)">—</span>
                    )}
                  </td>
                  <td className="py-1.5 pr-3 max-w-xs truncate font-mono text-xs text-muted"
                    title={it.output_path ?? ""}>
                    {it.output_filename ? (
                      <span className="text-success">{it.output_filename}</span>
                    ) : (
                      "—"
                    )}
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
  const countSheet = useCountVideoSheet(source.id);
  const push = useUiStore((s) => s.pushToast);
  const onErr = (e: unknown) => push("error", (e as ApiError).message);

  const cfg = source.config as Record<string, string>;
  const [connId, setConnId] = useState(cfg.connection_id ?? "");
  const [spreadsheetId, setSpreadsheetId] = useState(cfg.spreadsheet_id ?? "");
  const [worksheet, setWorksheet] = useState(cfg.worksheet ?? "");
  const [urlColumn, setUrlColumn] = useState(cfg.url_column ?? "VideoURL");
  const [titleColumn, setTitleColumn] = useState(cfg.title_column ?? "");
  const [filter, setFilter] = useState<NonNullable<SheetReadRequest["filter"]>>("all");
  const [limit, setLimit] = useState(0);
  const [writeback, setWriteback] = useState(Boolean(cfg.writeback));
  const [wbWorksheet, setWbWorksheet] = useState(cfg.writeback_worksheet ?? "");
  const [autoSync, setAutoSync] = useState(Boolean(cfg.auto_sync));
  const [autoInterval, setAutoInterval] = useState(Number(cfg.auto_sync_interval) || 600);
  const [autoRun, setAutoRun] = useState(Boolean(cfg.auto_run));
  const [count, setCount] = useState<{ matched: number; new: number; duplicate: number } | null>(
    null,
  );
  const [preview, setPreview] = useState<SheetPreviewRow[] | null>(null);

  const gsConns = (connections.data ?? []).filter((c) => c.provider === "google_sheets");
  const body = (): SheetReadRequest => ({ filter, limit: limit > 0 ? limit : null });

  const saveConfig = () =>
    update.mutateAsync({
      config: {
        connection_id: connId || undefined,
        spreadsheet_id: spreadsheetId.trim(),
        worksheet: worksheet.trim(),
        url_column: urlColumn.trim(),
        title_column: titleColumn.trim() || undefined,
        writeback,
        writeback_worksheet: wbWorksheet.trim() || undefined,
        auto_sync: autoSync,
        auto_sync_interval: autoInterval,
        auto_run: autoRun,
      },
    });

  const onSaveConfig = async () => {
    try {
      await saveConfig();
      push("success", autoSync ? "Đã lưu — sẽ tự đồng bộ định kỳ" : "Đã lưu cấu hình");
    } catch (e) {
      onErr(e);
    }
  };

  const onTest = () => {
    if (!connId) return push("error", "Chọn Connection trước");
    testConn.mutate(connId, {
      onSuccess: (r) => push(r.ok ? "success" : "error", r.message),
      onError: onErr,
    });
  };

  const onCount = async () => {
    try {
      await saveConfig();
      const c = await countSheet.mutateAsync(body());
      setCount(c);
      push("success", `Khớp ${c.matched} · mới ${c.new} · trùng ${c.duplicate}`);
    } catch (e) {
      onErr(e);
    }
  };

  const onRead = async () => {
    try {
      await saveConfig();
      const rows = await readSheet.mutateAsync(body());
      setPreview(rows);
      push("success", `Đọc Sheet: ${rows.length} video`);
    } catch (e) {
      onErr(e);
    }
  };

  const onImport = async () => {
    try {
      await saveConfig();
      const r = await importSheet.mutateAsync(body());
      setPreview(null);
      setCount(null);
      onImported();
      push("success", `Đã import ${r.imported} video (bỏ ${r.duplicates} trùng)`);
    } catch (e) {
      onErr(e);
    }
  };

  return (
    <div className="mb-4">
      <div className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-text">
        Google Sheets (nguồn link — Backend đọc, Agent không tham gia xem trước)
        <HelpTip id="google-sheets" />
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
          placeholder="Spreadsheet ID hoặc dán nguyên link Sheet" />
        <input className={INPUT} value={worksheet} onChange={(e) => setWorksheet(e.target.value)}
          placeholder="Worksheet (trống = sheet đầu)" />
        <input className={INPUT} value={urlColumn} onChange={(e) => setUrlColumn(e.target.value)}
          placeholder="Cột chứa Link Video (vd VideoURL)" />
        <input className={INPUT} value={titleColumn} onChange={(e) => setTitleColumn(e.target.value)}
          placeholder="Cột Tên (tuỳ chọn)" />
      </div>

      {/* Import Filter + Batch Import + Write-back */}
      <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
        <label className="flex items-center gap-1 text-muted">
          Lọc
          <select className="rounded border border-border bg-bg px-2 py-1 text-text"
            value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)}>
            {IMPORT_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 text-muted">
          Batch
          <select className="rounded border border-border bg-bg px-2 py-1 text-text"
            value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            {BATCH_LIMITS.map((b) => (
              <option key={b.value} value={b.value}>{b.label}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 text-muted" title="Ghi kết quả về Sheet sau khi tải xong">
          <input type="checkbox" checked={writeback} onChange={(e) => setWriteback(e.target.checked)} />
          Write-back
        </label>
        {writeback && (
          <input className="w-44 rounded border border-border bg-bg px-2 py-1 text-sm text-text"
            value={wbWorksheet} onChange={(e) => setWbWorksheet(e.target.value)}
            placeholder="Worksheet ghi (trống = cùng tab)" />
        )}
      </div>

      {/* Auto-Sync: web TỰ phát hiện sản phẩm mới trong Sheet (không tải lại video cũ) */}
      <div className="mt-2 flex flex-wrap items-center gap-2 rounded border border-border bg-bg p-2 text-sm">
        <label className="flex items-center gap-1 font-medium text-text" title="Tự quét Sheet định kỳ, chỉ nạp video mới (dedup bỏ video cũ)">
          <input type="checkbox" checked={autoSync} onChange={(e) => setAutoSync(e.target.checked)} />
          Tự đồng bộ (phát hiện video mới)
        </label>
        {autoSync && (
          <>
            <label className="flex items-center gap-1 text-muted">
              mỗi
              <select className="rounded border border-border bg-bg px-2 py-1 text-text"
                value={autoInterval} onChange={(e) => setAutoInterval(Number(e.target.value))}>
                <option value={300}>5 phút</option>
                <option value={600}>10 phút</option>
                <option value={1800}>30 phút</option>
                <option value={3600}>1 giờ</option>
              </select>
            </label>
            <label className="flex items-center gap-1 text-muted" title="Tải luôn video mới sau khi phát hiện">
              <input type="checkbox" checked={autoRun} onChange={(e) => setAutoRun(e.target.checked)} />
              Tự tải luôn
            </label>
          </>
        )}
        <button onClick={onSaveConfig} disabled={update.isPending}
          className="ml-auto rounded border border-border px-3 py-1 text-text hover:bg-border disabled:opacity-50">
          💾 Lưu cấu hình
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button onClick={onTest} disabled={testConn.isPending}
          className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border disabled:opacity-50">
          Kiểm tra kết nối
        </button>
        <HelpTip id="test-connection" />
        <button onClick={onCount} disabled={countSheet.isPending}
          className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border disabled:opacity-50">
          {countSheet.isPending ? "Đang đếm…" : "Đếm trước"}
        </button>
        <button onClick={onRead} disabled={readSheet.isPending}
          className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border disabled:opacity-50">
          {readSheet.isPending ? "Đang đọc…" : "Đọc Sheet (xem trước)"}
        </button>
        <button onClick={onImport} disabled={importSheet.isPending}
          className="rounded bg-primary px-3 py-1 text-sm text-white hover:bg-primary-hover disabled:opacity-50">
          {importSheet.isPending ? "Đang nhập…" : "Import (Nhập)"}
        </button>
        {count && (
          <span className="text-xs text-muted">
            Sẽ import <span className="font-semibold text-text">{count.new}</span> mới · trùng{" "}
            <span className="text-warning">{count.duplicate}</span> / khớp {count.matched}
          </span>
        )}
        {noConnHint(gsConns.length)}
      </div>

      {preview && (
        <div className="mt-3 max-h-60 overflow-auto rounded border border-border">
          <div className="bg-surface px-3 py-1 text-xs text-muted">
            Preview {preview.length} dòng (chưa import):
          </div>
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-muted">
              <tr className="border-b border-border">
                <th className="py-1 pl-3 pr-2">Dòng</th>
                <th className="py-1 pr-3">Title</th>
                <th className="py-1 pr-3">Source</th>
                <th className="py-1 pr-3">URL</th>
                <th className="py-1 pr-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {preview.map((r) => (
                <tr key={r.seq} className="border-b border-border/50">
                  <td className="py-1 pl-3 pr-2 text-muted">{r.sheet_row ?? r.seq + 1}</td>
                  <td className="py-1 pr-3 text-text">{r.title || "—"}</td>
                  <td className="py-1 pr-3 text-xs text-muted">{sourceHost(r.url)}</td>
                  <td className="py-1 pr-3 max-w-xs truncate font-mono text-xs text-muted" title={r.url}>
                    {r.url}
                  </td>
                  <td className="py-1 pr-3 text-xs text-muted">{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function sourceHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "—";
  }
}

function noConnHint(n: number) {
  if (n > 0) return null;
  return (
    <span className="text-xs text-muted">
      Chưa chọn Connection — hệ thống sẽ TỰ tạo từ gsa.json khi Read/Import.
    </span>
  );
}
