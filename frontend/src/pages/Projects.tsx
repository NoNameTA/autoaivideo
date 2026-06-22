import { useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import { useCreateProject, useDeleteProject, useProjects } from "../api/hooks";
import { Modal } from "../components/Modal";
import { SectionPanel } from "../components/SectionPanel";
import { ProjectForm } from "../components/forms/ProjectForm";
import { useUiStore } from "../store/ui";

export function Projects() {
  const { data, isLoading, isError, error } = useProjects();
  const create = useCreateProject();
  const remove = useDeleteProject();
  const push = useUiStore((s) => s.pushToast);
  const [open, setOpen] = useState(false);

  return (
    <SectionPanel
      title="Projects"
      description="Quản lý dự án → Batch → Job (SPEC 01 §5)."
      spec="SPEC 03 §3, 04 §2"
    >
      <div className="mb-4 flex justify-end">
        <button
          onClick={() => setOpen(true)}
          className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
        >
          + Dự án mới
        </button>
      </div>

      {isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {isError && (
        <p className="text-sm text-danger">Lỗi: {(error as ApiError)?.message ?? "không tải được"}</p>
      )}
      {data && data.items.length === 0 && (
        <p className="text-sm text-muted">Chưa có dự án. Tạo dự án đầu tiên để bắt đầu.</p>
      )}

      <ul className="flex flex-col gap-2">
        {data?.items.map((p) => (
          <li
            key={p.id}
            className="flex items-center justify-between rounded border border-border bg-bg p-3"
          >
            <div>
              <Link to={`/projects/${p.id}`} className="font-medium text-primary hover:underline">
                {p.name}
              </Link>
              <div className="text-xs text-muted">{p.default_pipeline}</div>
            </div>
            <button
              onClick={() =>
                remove.mutate(p.id, {
                  onSuccess: () => push("success", "Đã xoá dự án"),
                  onError: (e) => push("error", (e as ApiError).message),
                })
              }
              className="text-sm text-danger hover:underline"
            >
              Xoá
            </button>
          </li>
        ))}
      </ul>

      <Modal open={open} title="Tạo dự án" onClose={() => setOpen(false)}>
        <ProjectForm
          submitting={create.isPending}
          onSubmit={(values) =>
            create.mutate(values, {
              onSuccess: () => {
                setOpen(false);
                push("success", "Đã tạo dự án");
              },
              onError: (e) => push("error", (e as ApiError).message),
            })
          }
        />
      </Modal>
    </SectionPanel>
  );
}
