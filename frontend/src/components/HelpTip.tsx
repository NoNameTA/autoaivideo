import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { GUIDES } from "../help/guides";

/**
 * Biểu tượng hướng dẫn ⓘ — bấm để mở hộp hướng dẫn (Cách sử dụng + Tác dụng).
 * KHÔNG mở tab/đổi trang/reload. Nhỏ, đồng bộ Theme, không làm lệch bố cục.
 * Nội dung lấy từ kho tập trung `help/guides.ts` theo `id` (mở rộng = thêm mục, không sửa code).
 */
export function HelpTip({ id, className = "" }: { id: string; className?: string }) {
  const guide = GUIDES[id];
  const [open, setOpen] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });

  useLayoutEffect(() => {
    if (open && btnRef.current) {
      const r = btnRef.current.getBoundingClientRect();
      const width = 320;
      let left = r.left;
      if (left + width > window.innerWidth - 8) left = window.innerWidth - width - 8;
      setPos({ top: r.bottom + 6, left: Math.max(8, left) });
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!guide) return null;

  return (
    <>
      <button
        ref={btnRef}
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setOpen((v) => !v);
        }}
        aria-label={`Hướng dẫn: ${guide.title}`}
        title="Xem hướng dẫn"
        className={`inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-border text-[10px] leading-none text-muted hover:border-primary hover:text-primary ${className}`}
      >
        i
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-50" onClick={() => setOpen(false)} />
          <div
            className="fixed z-50 w-80 max-w-[92vw] rounded-lg border border-border bg-surface p-4 text-left shadow-xl"
            style={{ top: pos.top, left: pos.left }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label={`Hướng dẫn ${guide.title}`}
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold text-text">{guide.title}</span>
              <button
                onClick={() => setOpen(false)}
                aria-label="Đóng hướng dẫn"
                className="rounded p-0.5 text-muted hover:bg-border hover:text-text"
              >
                ✕
              </button>
            </div>

            <div className="mb-3">
              <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-primary">
                Cách sử dụng
              </div>
              <ol className="ml-4 list-decimal space-y-1 text-xs text-text">
                {guide.usage.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </div>

            <div>
              <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-success">
                Tác dụng
              </div>
              <p className="text-xs leading-relaxed text-muted">{guide.purpose}</p>
            </div>
          </div>
        </>
      )}
    </>
  );
}
