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

interface UiState {
  wsConnected: boolean;
  toasts: Toast[];
  activities: Activity[];
  setWsConnected: (v: boolean) => void;
  pushToast: (kind: ToastKind, message: string) => void;
  dismissToast: (id: string) => void;
  pushActivity: (a: Omit<Activity, "id" | "ts">) => void;
}

export const useUiStore = create<UiState>((set) => ({
  wsConnected: false,
  toasts: [],
  activities: [],
  setWsConnected: (wsConnected) => set({ wsConnected }),
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
