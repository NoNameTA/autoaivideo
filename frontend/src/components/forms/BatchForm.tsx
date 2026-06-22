import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { BatchCreate } from "../../types/api";

// Mỗi dòng là một JSON object = biến cho 1 job (SPEC 03 §5 InputImporter, 01 §6).
function parseRows(text: string): Record<string, unknown>[] | null {
  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length === 0) return null;
  const rows: Record<string, unknown>[] = [];
  for (const line of lines) {
    try {
      const obj = JSON.parse(line);
      if (typeof obj !== "object" || obj === null || Array.isArray(obj)) return null;
      rows.push(obj as Record<string, unknown>);
    } catch {
      return null;
    }
  }
  return rows;
}

const schema = z.object({
  name: z.string().min(1, "Bắt buộc").max(200),
  pipeline: z.string().optional(),
  inputs: z.string().refine((v) => parseRows(v) !== null, {
    message: "Mỗi dòng phải là 1 JSON object hợp lệ, tối thiểu 1 dòng",
  }),
});

type FormValues = z.infer<typeof schema>;

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-text";

export function BatchForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (values: BatchCreate) => void;
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
      pipeline: values.pipeline || undefined,
      inputs: parseRows(values.inputs) ?? [],
    });
  };

  return (
    <form onSubmit={handleSubmit(submit)} className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Tên lô
        <input className={INPUT} {...register("name")} />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Pipeline (trống = mặc định project)
        <input className={INPUT} {...register("pipeline")} placeholder="faceless_v1" />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Inputs — mỗi dòng 1 JSON object
        <textarea
          className={`${INPUT} h-32 font-mono text-xs`}
          {...register("inputs")}
          placeholder={'{"topic": "Video A"}\n{"topic": "Video B"}'}
        />
        {errors.inputs && <span className="text-xs text-danger">{errors.inputs.message}</span>}
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-primary px-4 py-2 text-white hover:bg-primary-hover disabled:opacity-50"
      >
        {submitting ? "Đang tạo lô…" : "Tạo lô"}
      </button>
    </form>
  );
}
