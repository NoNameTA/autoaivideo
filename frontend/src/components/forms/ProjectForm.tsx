import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { ProjectCreate } from "../../types/api";

const schema = z.object({
  name: z.string().min(1, "Tên không được trống").max(200),
  description: z.string().optional(),
  default_pipeline: z.string().min(1, "Bắt buộc"),
});

type FormValues = z.infer<typeof schema>;

const INPUT = "w-full rounded border border-border bg-bg px-3 py-2 text-text";

export function ProjectForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (values: ProjectCreate) => void;
  submitting: boolean;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { default_pipeline: "faceless_v1" },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Tên dự án
        <input className={INPUT} {...register("name")} />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Mô tả
        <input className={INPUT} {...register("description")} />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Pipeline mặc định
        <input className={INPUT} {...register("default_pipeline")} />
        {errors.default_pipeline && (
          <span className="text-xs text-danger">{errors.default_pipeline.message}</span>
        )}
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-primary px-4 py-2 text-white hover:bg-primary-hover disabled:opacity-50"
      >
        {submitting ? "Đang tạo…" : "Tạo dự án"}
      </button>
    </form>
  );
}
