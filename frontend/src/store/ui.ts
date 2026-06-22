import { create } from "zustand";

export type ToastKind = "success" | "error" | "info";

export interface Toast {
  id: string;
  kind: ToastKind;
  message: string;
}

interface UiState {
  wsConnected: boolean;
  toasts: Toast[];
  setWsConnected: (v: boolean) => void;
  pushToast: (kind: ToastKind, message: string) => void;
  dismissToast: (id: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  wsConnected: false,
  toasts: [],
  setWsConnected: (wsConnected) => set({ wsConnected }),
  pushToast: (kind, message) =>
    set((s) => ({
      toasts: [...s.toasts, { id: crypto.randomUUID(), kind, message }],
    })),
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
