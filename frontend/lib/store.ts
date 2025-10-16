import { create } from "zustand";

interface Settings {
  threshold: number;
  defaultK: number;
  defaultLiq: number;
  excludePemantauan: boolean;
  autoRefresh: boolean;
}

interface AppState {
  settings: Settings;
  updateSettings: (settings: Partial<Settings>) => void;
  notificationsEnabled: boolean;
  setNotificationsEnabled: (enabled: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  settings: {
    threshold: 0.75,
    defaultK: 50,
    defaultLiq: 0.5,
    excludePemantauan: true,
    autoRefresh: false,
  },
  updateSettings: (newSettings) =>
    set((state) => ({
      settings: { ...state.settings, ...newSettings },
    })),
  notificationsEnabled: false,
  setNotificationsEnabled: (enabled) => set({ notificationsEnabled: enabled }),
}));
