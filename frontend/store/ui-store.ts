/** Lightweight client-side UI state (Zustand). */
import { create } from "zustand";

interface UiState {
  /** Auto-refresh interval (ms) for dashboard queries. */
  refreshInterval: number;
  setRefreshInterval: (ms: number) => void;
}

export const useUiStore = create<UiState>((set) => ({
  refreshInterval: 10_000,
  setRefreshInterval: (ms) => set({ refreshInterval: ms }),
}));
