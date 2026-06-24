import { create } from "zustand";

export type ToastKind = "success" | "error" | "info";

export interface Toast {
  id: string;
  kind: ToastKind;
  message: string;
}

export type ActivityCategory = "job" | "plugin.runtime" | "plugin.lifecycle" | "fs" | "agent";

export interface Activity {
  id: string;
  category: ActivityCategory;
  kind: string;
  text: string;
  ts: number;
}

const ACTIVITY_LIMIT = 100;

export interface JobProgress {
  pct: number;
  msg: string;
}

interface UiState {
  wsConnected: boolean;
  toasts: Toast[];
  activities: Activity[];
  // Tiến độ download realtime theo job_id (cập nhật từ WS, không refetch).
  jobProgress: Record<string, JobProgress>;
  setWsConnected: (v: boolean) => void;
  pushToast: (kind: ToastKind, message: string) => void;
  dismissToast: (id: string) => void;
  pushActivity: (a: Omit<Activity, "id" | "ts">) => void;
  setJobProgress: (jobId: string, p: JobProgress) => void;
}

export const useUiStore = create<UiState>((set) => ({
  wsConnected: false,
  toasts: [],
  activities: [],
  jobProgress: {},
  setWsConnected: (wsConnected) => set({ wsConnected }),
  setJobProgress: (jobId, p) =>
    set((s) => ({ jobProgress: { ...s.jobProgress, [jobId]: p } })),
  pushToast: (kind, message) =>
    set((s) => ({
      toasts: [...s.toasts, { id: crypto.randomUUID(), kind, message }],
    })),
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  pushActivity: (a) =>
    set((s) => ({
      activities: [
        { ...a, id: crypto.randomUUID(), ts: Date.now() },
        ...s.activities,
      ].slice(0, ACTIVITY_LIMIT),
    })),
}));
