import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { PluginRegister } from "../../types/api";

const schema = z.object({
  name: z.string().min(1, "Bắt buộc").max(100),
  version: z.string().optional(),
  capability: z.string().optional(),
  type: z.string().optional(),
  manifest: z
    .string()
    .optional()
    .refine(
      (v) => {
        if (!v || v.trim() === "") return true;
        try {
          JSON.parse(v);
          return true;
        } catch {
          return false;
        }
      },
      { message: "Manifest phải là JSON hợp lệ" },
    ),
});

type FormValues = z.infer<typeof schema>;

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-text";

export function PluginForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (values: PluginRegister) => void;
  submitting: boolean;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const submit = (values: FormValues) => {
    onSubmit({
      name: values.name,
      version: values.version,
      capability: values.capability,
      type: values.type,
      manifest: values.manifest ? JSON.parse(values.manifest) : {},
    });
  };

  return (
    <form onSubmit={handleSubmit(submit)} className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Tên plugin
        <input className={INPUT} {...register("name")} />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>
      <div className="grid grid-cols-3 gap-2">
        <label className="flex flex-col gap-1 text-sm">
          Version
          <input className={INPUT} {...register("version")} />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Capability
          <input className={INPUT} {...register("capability")} />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Type
          <input className={INPUT} {...register("type")} placeholder="cli-process" />
        </label>
      </div>
      <label className="flex flex-col gap-1 text-sm">
        Manifest (JSON)
        <textarea
          className={`${INPUT} h-24 font-mono text-xs`}
          {...register("manifest")}
          placeholder='{"config_schema": {"type": "object"}}'
        />
        {errors.manifest && (
          <span className="text-xs text-danger">{errors.manifest.message}</span>
        )}
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-primary px-4 py-2 text-white hover:bg-primary-hover disabled:opacity-50"
      >
        {submitting ? "Đang đăng ký…" : "Đăng ký plugin"}
      </button>
    </form>
  );
}
