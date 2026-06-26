import { useState } from "react";

import { ApiError } from "../api/client";
import { endpoints } from "../api/endpoints";
import {
  usePlugins,
  useRegisterPlugin,
  useRemovePlugin,
  useUpdatePlugin,
} from "../api/hooks";
import { Modal } from "../components/Modal";
import { SectionPanel } from "../components/SectionPanel";
import { PluginForm } from "../components/forms/PluginForm";
import { useUiStore } from "../store/ui";

export function Plugins() {
  const { data, isLoading } = usePlugins();
  const register = useRegisterPlugin();
  const update = useUpdatePlugin();
  const remove = useRemovePlugin();
  const push = useUiStore((s) => s.pushToast);

  const [open, setOpen] = useState(false);
  const [schema, setSchema] = useState<{ name: string; schema: Record<string, unknown> } | null>(
    null,
  );

  const onError = (e: unknown) => push("error", (e as ApiError).message);

  return (
    <SectionPanel
      title="Quản lý Plugin"
      help="plugins"
      description="Cài / Bật / Tắt / Gỡ plugin (SPEC 08)."
      spec="SPEC 08, 03 §5"
    >
      <div className="mb-4 flex justify-end">
        <button
          onClick={() => setOpen(true)}
          className="rounded bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover"
        >
          + Đăng ký plugin
        </button>
      </div>

      {isLoading && <p className="text-sm text-muted">Đang tải…</p>}
      {data && data.length === 0 && <p className="text-sm text-muted">Chưa có plugin.</p>}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {data?.map((p) => (
          <div key={p.name} className="rounded-lg border border-border bg-bg p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-text">{p.name}</div>
              <span className={p.enabled ? "text-success" : "text-muted"}>
                {p.enabled ? "● bật" : "○ tắt"}
              </span>
            </div>
            <div className="mt-1 text-xs text-muted">
              {p.capability || "?"} · {p.type || "?"} · v{p.version || "?"}
            </div>
            <div className="mt-3 flex gap-3 text-sm">
              <button
                onClick={() =>
                  update.mutate(
                    { name: p.name, enabled: !p.enabled },
                    { onSuccess: () => push("success", "Đã cập nhật"), onError },
                  )
                }
                className="text-primary hover:underline"
              >
                {p.enabled ? "Tắt" : "Bật"}
              </button>
              <button
                onClick={async () => {
                  try {
                    setSchema(await endpoints.getPluginSchema(p.name));
                  } catch (e) {
                    onError(e);
                  }
                }}
                className="text-primary hover:underline"
              >
                Schema
              </button>
              <button
                onClick={() =>
                  remove.mutate(p.name, {
                    onSuccess: () => push("success", "Đã gỡ plugin"),
                    onError,
                  })
                }
                className="text-danger hover:underline"
              >
                Gỡ
              </button>
            </div>
          </div>
        ))}
      </div>

      <Modal open={open} title="Đăng ký plugin" onClose={() => setOpen(false)}>
        <PluginForm
          submitting={register.isPending}
          onSubmit={(values) =>
            register.mutate(values, {
              onSuccess: () => {
                setOpen(false);
                push("success", "Đã đăng ký plugin");
              },
              onError,
            })
          }
        />
      </Modal>

      <Modal open={schema !== null} title={`Schema: ${schema?.name}`} onClose={() => setSchema(null)}>
        <pre className="max-h-80 overflow-auto rounded bg-bg p-3 text-xs text-text">
          {JSON.stringify(schema?.schema, null, 2)}
        </pre>
      </Modal>
    </SectionPanel>
  );
}
