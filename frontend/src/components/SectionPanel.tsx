import type { ReactNode } from "react";

import { HelpTip } from "./HelpTip";

interface Props {
  title: string;
  description?: string;
  spec?: string;
  /** id hướng dẫn (help/guides.ts) — hiện biểu tượng ⓘ cạnh tiêu đề. */
  help?: string;
  children?: ReactNode;
}

/** Khung trang chuẩn (SPEC 12). Mỗi trang dùng để hiển thị tiêu đề + nội dung. */
export function SectionPanel({ title, description, spec, help, children }: Props) {
  return (
    <section>
      <header className="mb-4">
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-text">
          {title}
          {help && <HelpTip id={help} className="h-5 w-5 text-xs" />}
        </h1>
        {description && <p className="mt-1 text-muted">{description}</p>}
        {spec && <p className="mt-1 text-xs text-muted">Tham chiếu: {spec}</p>}
      </header>
      <div className="rounded-lg border border-border bg-surface p-5">{children}</div>
    </section>
  );
}
