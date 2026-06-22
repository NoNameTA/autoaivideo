import { useEffect } from "react";
import { useUiStore } from "../store/ui";

const BORDER: Record<string, string> = {
  success: "border-success",
  error: "border-danger",
  info: "border-info",
};

const TOAST_TTL_MS = 4000;

export function Toaster() {
  const toasts = useUiStore((s) => s.toasts);
  const dismiss = useUiStore((s) => s.dismissToast);

  useEffect(() => {
    const timers = toasts.map((t) => setTimeout(() => dismiss(t.id), TOAST_TTL_MS));
    return () => timers.forEach(clearTimeout);
  }, [toasts, dismiss]);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <button
          key={t.id}
          onClick={() => dismiss(t.id)}
          className={`rounded border-l-4 bg-surface px-4 py-2 text-left text-sm text-text shadow ${BORDER[t.kind]}`}
        >
          {t.message}
        </button>
      ))}
    </div>
  );
}
