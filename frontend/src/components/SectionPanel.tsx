import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  spec?: string;
  children?: ReactNode;
}

/** Khung trang chuẩn (SPEC 12). Mỗi trang dùng để hiển thị tiêu đề + nội dung. */
export function SectionPanel({ title, description, spec, children }: Props) {
  return (
    <section>
      <header className="mb-4">
        <h1 className="text-2xl font-semibold text-text">{title}</h1>
        {description && <p className="mt-1 text-muted">{description}</p>}
        {spec && <p className="mt-1 text-xs text-muted">Tham chiếu: {spec}</p>}
      </header>
      <div className="rounded-lg border border-border bg-surface p-5">{children}</div>
    </section>
  );
}
