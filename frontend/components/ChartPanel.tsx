"use client";

import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { fetchEquity } from "@/lib/api";

interface ChartPanelProps {
  metrics: any;
  k: number;
}

export default function ChartPanel({ metrics, k }: ChartPanelProps) {
  const [activeTab, setActiveTab] = useState<"valid" | "test" | "live">("valid");
  const { data: equityData } = useSWR(["equity", k], () => fetchEquity(k));
  const chartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!chartRef.current || !equityData) return;

    const canvas = chartRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth * 2;
    canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);

    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    const padding = 40;

    ctx.clearRect(0, 0, width, height);

    const equity = equityData.equity || [];
    const min = Math.min(...equity);
    const max = Math.max(...equity);

    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.beginPath();

    equity.forEach((val: number, i: number) => {
      const x = padding + (i / (equity.length - 1)) * (width - padding * 2);
      const y = height - padding - ((val - min) / (max - min)) * (height - padding * 2);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();

    ctx.fillStyle = "#888";
    ctx.font = "12px sans-serif";
    ctx.fillText(min.toFixed(2), 5, height - padding);
    ctx.fillText(max.toFixed(2), 5, padding);
  }, [equityData]);

  return (
    <div className="bg-card border border-border rounded-lg p-6 space-y-4">
      <h2 className="text-xl font-semibold">Metrics & Charts</h2>

      {metrics && (
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">AP Valid:</span>
            <span className="font-bold">{metrics.ap_valid?.toFixed(4) || "N/A"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">AP Test:</span>
            <span className="font-bold">{metrics.ap_test?.toFixed(4) || "N/A"}</span>
          </div>
        </div>
      )}

      <div className="flex gap-2 border-b border-border">
        {(["valid", "test", "live"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 capitalize transition ${
              activeTab === tab
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="h-64 bg-background rounded border border-border">
        <canvas ref={chartRef} className="w-full h-full" />
      </div>
    </div>
  );
}
