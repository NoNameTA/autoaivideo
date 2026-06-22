import type { Step } from "../types/api";
import { statusStyle } from "../lib/format";

// Timeline ngang các step (SPEC 03 §5, 12 §5).
export function StepTimeline({ steps }: { steps: Step[] }) {
  if (steps.length === 0) {
    return <p className="text-sm text-muted">Job chưa có step.</p>;
  }
  return (
    <ol className="flex flex-wrap gap-2">
      {steps.map((step) => {
        const s = statusStyle(step.status);
        return (
          <li
            key={step.id}
            className="min-w-[120px] flex-1 rounded border border-border bg-bg p-3"
            title={step.error ?? step.adapter}
          >
            <div className="text-xs text-muted">{step.order + 1}. {step.adapter}</div>
            <div className="font-medium text-text">{step.step_key}</div>
            <div className={`mt-1 text-sm ${s.color}`}>
              {s.icon} {s.label}
            </div>
            {step.error && <div className="mt-1 text-xs text-danger">{step.error}</div>}
          </li>
        );
      })}
    </ol>
  );
}
