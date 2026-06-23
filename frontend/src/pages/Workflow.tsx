import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { endpoints } from "../api/endpoints";
import {
  useDeletePipeline,
  usePipelines,
  usePlugins,
  useProjects,
  useSavePipeline,
} from "../api/hooks";
import { Modal } from "../components/Modal";
import { SectionPanel } from "../components/SectionPanel";
import { useUiStore } from "../store/ui";
import type { Pipeline, StepDef } from "../types/pipeline";

interface EditStep {
  step_key: string;
  adapter: string;
  configText: string;
}

const BASE_ADAPTERS = [
  "cli.run",
  "video.ffmpeg",
  "media.download",
  "web.cdp",
  "web.cdp.edge",
  "desktop.notepad",
];
const INPUT = "w-full rounded border border-border bg-bg px-2 py-1 text-sm text-text";

export function Workflow() {
  const pipelines = usePipelines();
  const plugins = usePlugins();
  const projects = useProjects();
  const save = useSavePipeline();
  const remove = useDeletePipeline();
  const push = useUiStore((s) => s.pushToast);
  const navigate = useNavigate();

  const [editor, setEditor] = useState<{ editing: boolean; name: string } | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [steps, setSteps] = useState<EditStep[]>([]);
  const [runFor, setRunFor] = useState<Pipeline | null>(null);
  const [runProject, setRunProject] = useState("");
  const [runInputs, setRunInputs] = useState("");

  const adapters = Array.from(
    new Set([...BASE_ADAPTERS, ...(plugins.data?.map((p) => p.capability) ?? [])]),
  ).filter(Boolean);

  const onError = (e: unknown) => push("error", (e as ApiError).message);

  const openCreate = () => {
    setEditor({ editing: false, name: "" });
    setName("");
    setDesc("");
    setSteps([{ step_key: "step1", adapter: "cli.run", configText: "{}" }]);
  };

  const openEdit = (p: Pipeline) => {
    setEditor({ editing: true, name: p.name });
    setName(p.name);
    setDesc(p.description);
    setSteps(
      p.steps.map((s: StepDef) => ({
        step_key: s.step_key,
        adapter: s.adapter,
        configText: JSON.stringify(s.config ?? {}, null, 0),
      })),
    );
  };

  const setStep = (i: number, patch: Partial<EditStep>) =>
    setSteps((prev) => prev.map((s, idx) => (idx === i ? { ...s, ...patch } : s)));
  const addStep = () =>
    setSteps((prev) => [...prev, { step_key: `step${prev.length + 1}`, adapter: "cli.run", configText: "{}" }]);
  const removeStep = (i: number) => setSteps((prev) => prev.filter((_, idx) => idx !== i));
  const moveStep = (i: number, dir: -1 | 1) =>
    setSteps((prev) => {
      const j = i + dir;
      if (j < 0 || j >= prev.length) return prev;
      const next = [...prev];
      [next[i], next[j]] = [next[j], next[i]];
      return next;
    });

  const submitEditor = () => {
    if (!editor) return;
    if (!editor.editing && !/^[A-Za-z0-9_-]+$/.test(name)) {
      push("error", "Tên chỉ gồm chữ/số/_/- và không trống");
      return;
    }
    const parsed: StepDef[] = [];
    for (const s of steps) {
      if (!s.step_key.trim() || !s.adapter.trim()) {
        push("error", "Mỗi step cần step_key và adapter");
        return;
      }
      try {
        parsed.push({ step_key: s.step_key, adapter: s.adapter, config: JSON.parse(s.configText || "{}") });
      } catch {
        push("error", `Config của step "${s.step_key}" không phải JSON hợp lệ`);
        return;
      }
    }
    if (parsed.length === 0) {
      push("error", "Cần ít nhất 1 step");
      return;
    }
    save.mutate(
      { editing: editor.editing, name, data: { description: desc, steps: parsed } },
      {
        onSuccess: () => {
          setEditor(null);
          push("success", editor.editing ? "Đã cập nhật pipeline" : "Đã tạo pipeline");
        },
        onError,
      },
    );
  };

  const submitRun = () => {
    if (!runFor || !runProject) {
      push("error", "Chọn dự án để chạy");
      return;
    }
    const inputs = runInputs
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      });
    if (inputs.length === 0 || inputs.some((x) => x === null)) {
      push("error", "Mỗi dòng input phải là 1 JSON object, tối thiểu 1 dòng");
      return;
    }
    endpoints
      .runPipeline(runFor.name, { project_id: runProject, name: `Run ${runFor.name}`, inputs })
      .then((batch) => {
        setRunFor(null);
        push("success", "Đã chạy workflow");
        navigate(`/batches/${batch.id}`);
      })
      .catch(onError);
  };

  return (
    <SectionPanel
      title="Workflow"
      description="Tạo / chỉnh sửa / chạy pipeline và theo dõi trạng thái từng bước (SPEC 02 §4)."
      spec="SPEC 02 §4, 03 §5"
    >
      <div className="mb-4 flex justify-end">
        <button
          onClick={openCreate}
          className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
        >
          + Pipeline mới
        </button>
      </div>

      {pipelines.isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {pipelines.isError && (
        <p className="text-sm text-danger">Lỗi: {(pipelines.error as ApiError)?.message}</p>
      )}
      {pipelines.data && pipelines.data.length === 0 && (
        <p className="text-sm text-muted">Chưa có pipeline. Tạo pipeline đầu tiên.</p>
      )}

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {pipelines.data?.map((p) => (
          <div key={p.id} className="rounded-lg border border-border bg-bg p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-text">{p.name}</div>
              {p.builtin && (
                <span className="rounded bg-border px-2 py-0.5 text-xs text-muted">built-in</span>
              )}
            </div>
            <div className="mt-1 text-xs text-muted">{p.description || "—"}</div>
            <ol className="mt-3 flex flex-wrap items-center gap-1">
              {p.steps.map((s, i) => (
                <li key={i} className="flex items-center gap-1">
                  <span
                    className="rounded border border-border px-2 py-1 text-xs"
                    title={s.adapter}
                  >
                    {i + 1}. {s.step_key}
                    <span className="ml-1 text-muted">({s.adapter})</span>
                  </span>
                  {i < p.steps.length - 1 && <span className="text-muted">→</span>}
                </li>
              ))}
            </ol>
            <div className="mt-3 flex gap-3 text-sm">
              <button onClick={() => { setRunFor(p); setRunProject(""); setRunInputs(""); }} className="text-primary hover:underline">
                Run
              </button>
              <button onClick={() => openEdit(p)} className="text-primary hover:underline">
                Sửa
              </button>
              <button
                onClick={() =>
                  remove.mutate(p.name, {
                    onSuccess: () => push("success", "Đã xoá pipeline"),
                    onError,
                  })
                }
                className="text-danger hover:underline"
              >
                Xoá
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Editor */}
      <Modal
        open={editor !== null}
        title={editor?.editing ? `Sửa pipeline: ${editor.name}` : "Pipeline mới"}
        onClose={() => setEditor(null)}
      >
        <datalist id="adapter-list">
          {adapters.map((a) => (
            <option key={a} value={a} />
          ))}
        </datalist>
        <div className="flex flex-col gap-3">
          {!editor?.editing && (
            <label className="flex flex-col gap-1 text-sm">
              Tên (chữ/số/_/-)
              <input className={INPUT} value={name} onChange={(e) => setName(e.target.value)} />
            </label>
          )}
          <label className="flex flex-col gap-1 text-sm">
            Mô tả
            <input className={INPUT} value={desc} onChange={(e) => setDesc(e.target.value)} />
          </label>

          <div className="text-sm font-semibold text-text">Steps</div>
          <div className="flex max-h-72 flex-col gap-2 overflow-auto">
            {steps.map((s, i) => (
              <div key={i} className="rounded border border-border p-2">
                <div className="mb-1 flex items-center gap-1">
                  <span className="text-xs text-muted">#{i + 1}</span>
                  <button onClick={() => moveStep(i, -1)} className="ml-auto text-xs text-muted hover:text-text">↑</button>
                  <button onClick={() => moveStep(i, 1)} className="text-xs text-muted hover:text-text">↓</button>
                  <button onClick={() => removeStep(i)} className="text-xs text-danger">✕</button>
                </div>
                <div className="grid grid-cols-2 gap-1">
                  <input
                    className={INPUT}
                    placeholder="step_key"
                    value={s.step_key}
                    onChange={(e) => setStep(i, { step_key: e.target.value })}
                  />
                  <input
                    className={INPUT}
                    list="adapter-list"
                    placeholder="adapter"
                    value={s.adapter}
                    onChange={(e) => setStep(i, { adapter: e.target.value })}
                  />
                </div>
                <textarea
                  className={`${INPUT} mt-1 h-14 font-mono text-xs`}
                  placeholder='config JSON, vd {"command":["python","-c","1"]}'
                  value={s.configText}
                  onChange={(e) => setStep(i, { configText: e.target.value })}
                />
              </div>
            ))}
          </div>
          <button onClick={addStep} className="rounded border border-border px-3 py-1 text-sm text-text hover:bg-border">
            + Thêm step
          </button>

          <button
            onClick={submitEditor}
            disabled={save.isPending}
            className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
          >
            {save.isPending ? "Đang lưu…" : "Lưu pipeline"}
          </button>
        </div>
      </Modal>

      {/* Run */}
      <Modal open={runFor !== null} title={`Chạy: ${runFor?.name}`} onClose={() => setRunFor(null)}>
        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Dự án
            <select className={INPUT} value={runProject} onChange={(e) => setRunProject(e.target.value)}>
              <option value="">— chọn dự án —</option>
              {projects.data?.items.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            {projects.data?.items.length === 0 && (
              <span className="text-xs text-warning">Chưa có dự án — tạo ở trang Projects trước.</span>
            )}
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Inputs — mỗi dòng 1 JSON object
            <textarea
              className={`${INPUT} h-28 font-mono text-xs`}
              value={runInputs}
              onChange={(e) => setRunInputs(e.target.value)}
              placeholder={'{"topic": "A"}\n{"topic": "B"}'}
            />
          </label>
          <button
            onClick={submitRun}
            className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
          >
            Chạy workflow
          </button>
        </div>
      </Modal>
    </SectionPanel>
  );
}
