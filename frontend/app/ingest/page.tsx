"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Upload, FileText, Image, FileAudio, Clipboard, Globe } from "lucide-react";

const API_BASE = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_BACKEND_URL || '') : '';

export default function IngestPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"upload" | "audio" | "paste" | "scrape">("upload");
  const [market, setMarket] = useState("ID");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [tickers, setTickers] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (endpoint: string) => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setLoading(true);
    setProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("market", market);

      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePaste = async () => {
    if (!text.trim()) {
      setError("Please paste some text");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("text", text);
      formData.append("market", market);

      const response = await fetch(`${API_BASE}/ingest/paste`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Paste failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async () => {
    if (!tickers.trim()) {
      setError("Please enter tickers");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/ingest/scrape?source=yahoo&market=${market}&tickers=${tickers}`,
        { method: "POST" }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Scrape failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <h1 className="text-4xl font-bold">Data Ingest Wizard</h1>

        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Market</label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="w-full bg-background border border-border rounded px-3 py-2"
            >
              <option value="ID">Indonesia (IDX)</option>
              <option value="US">United States</option>
            </select>
          </div>

          <div className="flex gap-2 border-b border-border">
            {[
              { key: "upload", label: "Upload", icon: Upload },
              { key: "audio", label: "Audio", icon: FileAudio },
              { key: "paste", label: "Paste", icon: Clipboard },
              { key: "scrape", label: "Auto", icon: Globe },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex items-center gap-2 px-4 py-2 transition ${
                  activeTab === tab.key
                    ? "border-b-2 border-primary text-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="min-h-[300px]">
            {activeTab === "upload" && (
              <div className="space-y-4">
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls,.pdf,.png,.jpg,.jpeg,.docx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full"
                />

                {file && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        const ext = file.name.split(".").pop()?.toLowerCase();
                        if (ext === "csv") handleFileUpload("/ingest/csv");
                        else if (ext === "xlsx" || ext === "xls") handleFileUpload("/ingest/excel");
                        else if (ext === "pdf") handleFileUpload("/ingest/pdf");
                        else if (ext === "png" || ext === "jpg" || ext === "jpeg") handleFileUpload("/ingest/image");
                        else if (ext === "docx") handleFileUpload("/ingest/docx");
                      }}
                      disabled={loading}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition disabled:opacity-50"
                    >
                      {loading ? "Uploading..." : "Upload"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === "audio" && (
              <div className="space-y-4">
                <p className="text-muted-foreground">Audio transcription coming soon...</p>
              </div>
            )}

            {activeTab === "paste" && (
              <div className="space-y-4">
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste your data here (CSV, TSV, or space-separated)"
                  className="w-full h-48 bg-background border border-border rounded px-3 py-2 font-mono text-sm"
                />
                <button
                  onClick={handlePaste}
                  disabled={loading}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition disabled:opacity-50"
                >
                  {loading ? "Processing..." : "Submit"}
                </button>
              </div>
            )}

            {activeTab === "scrape" && (
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Auto-fetch latest EOD data from Yahoo Finance
                </p>
                <input
                  type="text"
                  value={tickers}
                  onChange={(e) => setTickers(e.target.value)}
                  placeholder="Enter tickers (comma-separated): BBCA,BBRI,TLKM"
                  className="w-full bg-background border border-border rounded px-3 py-2"
                />
                <button
                  onClick={handleScrape}
                  disabled={loading}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition disabled:opacity-50"
                >
                  {loading ? "Fetching..." : "Fetch Data"}
                </button>
              </div>
            )}
          </div>

          {loading && progress > 0 && (
            <div className="space-y-2">
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-center text-muted-foreground">{progress}%</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive rounded text-destructive">
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-4 p-4 bg-muted rounded">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Ingest Complete</h3>
                <span
                  className={`px-2 py-1 rounded text-sm ${
                    result.status === "valid"
                      ? "bg-green-500/20 text-green-400"
                      : result.status === "warning"
                      ? "bg-yellow-500/20 text-yellow-400"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {result.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Dataset ID:</span>
                  <p className="font-mono">{result.dataset_id}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Rows:</span>
                  <p>{result.row_count}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Tickers:</span>
                  <p>{result.ticker_count}</p>
                </div>
              </div>

              {result.validation && (
                <div className="space-y-2 text-sm">
                  {result.validation.errors && result.validation.errors.length > 0 && (
                    <div>
                      <p className="font-medium text-destructive">Errors:</p>
                      <ul className="list-disc list-inside">
                        {result.validation.errors.map((err: string, i: number) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.validation.warnings && result.validation.warnings.length > 0 && (
                    <div>
                      <p className="font-medium text-yellow-400">Warnings:</p>
                      <ul className="list-disc list-inside">
                        {result.validation.warnings.map((warn: string, i: number) => (
                          <li key={i}>{warn}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={() => router.push("/dashboard")}
                className="w-full px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition"
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
