"use client";

import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function SettingsPage() {
  const { settings, updateSettings } = useStore();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <h1 className="text-4xl font-bold">Settings</h1>

        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Alert Threshold</label>
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={settings.threshold}
              onChange={(e) => updateSettings({ threshold: Number(e.target.value) })}
              className="w-full bg-background border border-border rounded px-3 py-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Probability threshold for alerts (0-1)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Default Top K</label>
            <select
              value={settings.defaultK}
              onChange={(e) => updateSettings({ defaultK: Number(e.target.value) })}
              className="w-full bg-background border border-border rounded px-3 py-2"
            >
              {[10, 20, 30, 50, 100].map((val) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Default Min Liquidity: {settings.defaultLiq.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={settings.defaultLiq}
              onChange={(e) => updateSettings({ defaultLiq: Number(e.target.value) })}
              className="w-full"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.excludePemantauan}
                onChange={(e) => updateSettings({ excludePemantauan: e.target.checked })}
                className="w-4 h-4"
              />
              <span className="text-sm">Default: Exclude Pemantauan Khusus</span>
            </label>
          </div>

          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoRefresh}
                onChange={(e) => updateSettings({ autoRefresh: e.target.checked })}
                className="w-4 h-4"
              />
              <span className="text-sm">Auto-refresh data every 30s</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
