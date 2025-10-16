"use client";

import { useState, useEffect } from "react";
import { useStore } from "@/lib/store";
import useSWR from "swr";
import { fetchScoreLatest, fetchMetrics, createSSEConnection } from "@/lib/api";
import FilterPanel from "@/components/FilterPanel";
import CandidatesTable from "@/components/CandidatesTable";
import ChartPanel from "@/components/ChartPanel";
import AlertBar from "@/components/AlertBar";
import { Bell, Upload } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { settings, notificationsEnabled, setNotificationsEnabled } = useStore();
  const [market, setMarket] = useState("ID");
  const [k, setK] = useState(settings.defaultK);
  const [liq, setLiq] = useState(settings.defaultLiq);
  const [excludePemantauan, setExcludePemantauan] = useState(settings.excludePemantauan);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [highlightedTickers, setHighlightedTickers] = useState<Set<string>>(new Set());

  const { data: scores, error, isLoading } = useSWR(
    ["score_latest", market, k, liq, excludePemantauan],
    () => fetchScoreLatest(k, liq, excludePemantauan, market),
    { refreshInterval: settings.autoRefresh ? 30000 : 0 }
  );

  const { data: metrics } = useSWR("metrics", fetchMetrics);

  useEffect(() => {
    const eventSource = createSSEConnection((data) => {
      setAlerts((prev) => [data, ...prev].slice(0, 5));
      setHighlightedTickers((prev) => new Set(prev).add(data.ticker));
      setTimeout(() => {
        setHighlightedTickers((prev) => {
          const next = new Set(prev);
          next.delete(data.ticker);
          return next;
        });
      }, 3000);

      if (notificationsEnabled && "Notification" in window && Notification.permission === "granted") {
        new Notification("ARA Alert", {
          body: `${data.ticker} - Proba: ${data.proba.toFixed(4)}`,
          icon: "/icon-192.png",
        });
      }
    });

    return () => eventSource.close();
  }, [notificationsEnabled]);

  const handleEnableNotifications = async () => {
    if (!("Notification" in window)) {
      alert("Browser tidak mendukung notifikasi");
      return;
    }

    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      setNotificationsEnabled(true);
      new Notification("ARA Radar", { body: "Notifikasi telah diaktifkan" });
    }
  };

  const downloadCSV = () => {
    if (!scores?.rows) return;
    const headers = ["Rank", "Ticker", "Proba", "Nama", "Papan", "VolRank"];
    const csvContent = [
      headers.join(","),
      ...scores.rows.map((r: any, i: number) =>
        [
          i + 1,
          r.Ticker || "",
          r.proba_ARA_t1 || 0,
          r.nama || "",
          r.Papan || "",
          r.vol_rank_day || 0,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ara_candidates_${scores.date}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <AlertBar alerts={alerts} />

      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-4xl font-bold">ARA Radar Dashboard</h1>
          <select
            value={market}
            onChange={(e) => setMarket(e.target.value)}
            className="bg-card border border-border rounded px-3 py-2"
          >
            <option value="ID">Indonesia</option>
            <option value="US">United States</option>
          </select>
        </div>
        <div className="flex gap-2">
          <Link
            href="/ingest"
            className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition"
          >
            <Upload className="w-5 h-5" />
            Ingest Data
          </Link>
          <button
            onClick={handleEnableNotifications}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
          >
            <Bell className="w-5 h-5" />
            {notificationsEnabled ? "Notifikasi Aktif" : "Aktifkan Notifikasi"}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <FilterPanel
            k={k}
            setK={setK}
            liq={liq}
            setLiq={setLiq}
            excludePemantauan={excludePemantauan}
            setExcludePemantauan={setExcludePemantauan}
            onDownload={downloadCSV}
          />

          <CandidatesTable
            data={scores?.rows || []}
            date={scores?.date || ""}
            isLoading={isLoading}
            error={error}
            highlightedTickers={highlightedTickers}
          />
        </div>

        <div>
          <ChartPanel metrics={metrics} k={k} />
        </div>
      </div>
    </div>
  );
}
