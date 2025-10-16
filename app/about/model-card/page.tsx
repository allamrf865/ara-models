"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { fetchModelCard } from "@/lib/api";
import { ArrowLeft } from "lucide-react";

export default function ModelCardPage() {
  const router = useRouter();
  const { data, error, isLoading } = useSWR("model_card", fetchModelCard);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading model card...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="bg-card border border-destructive rounded-lg p-6 text-center text-destructive">
            Error loading model card: {error.message}
          </div>
        </div>
      </div>
    );
  }

  const card = data?.card || {};
  const metrics = card.metrics || {};

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

        <h1 className="text-4xl font-bold">Model Card</h1>

        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
          <div>
            <h2 className="text-xl font-semibold mb-2">Model Information</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Model Type:</span>
                <span>{card.model_type || "XGBoost Ensemble"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Version:</span>
                <span>{card.version || "N/A"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Features:</span>
                <span>{data?.required_features_count || 0}</span>
              </div>
            </div>
          </div>

          <div className="border-t border-border pt-4">
            <h2 className="text-xl font-semibold mb-2">Performance Metrics</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">AP Validation:</span>
                <span className="font-bold">{metrics.ap_valid?.toFixed(4) || "N/A"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">AP Test:</span>
                <span className="font-bold">{metrics.ap_test?.toFixed(4) || "N/A"}</span>
              </div>
            </div>
          </div>

          {metrics.p_at_k && Object.keys(metrics.p_at_k).length > 0 && (
            <div className="border-t border-border pt-4">
              <h2 className="text-xl font-semibold mb-2">Precision @ K</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(metrics.p_at_k).map(([k, val]) => (
                  <div key={k} className="text-center p-3 bg-muted rounded">
                    <div className="text-xs text-muted-foreground">P@{k}</div>
                    <div className="text-lg font-bold">{(val as number).toFixed(3)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-border pt-4">
            <h2 className="text-xl font-semibold mb-2">Raw JSON</h2>
            <pre className="bg-background p-4 rounded border border-border text-xs overflow-x-auto">
              {JSON.stringify(card, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
