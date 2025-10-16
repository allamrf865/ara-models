const API_BASE = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_BACKEND_URL || '')
  : '';

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/health`);
  if (!r.ok) throw new Error("Health check failed");
  return r.json();
}

export async function fetchMetrics() {
  const r = await fetch(`${API_BASE}/metrics`);
  if (!r.ok) throw new Error("Failed to fetch metrics");
  return r.json();
}

export async function fetchScoreLatest(k: number, liq: number, excludePemantauan: boolean) {
  const params = new URLSearchParams({
    k: k.toString(),
    liq: liq.toString(),
    exclude_pemantauan: excludePemantauan.toString(),
  });
  const r = await fetch(`${API_BASE}/score_latest?${params}`);
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

export async function fetchEquity(k: number) {
  const params = new URLSearchParams({ k: k.toString() });
  const r = await fetch(`${API_BASE}/equity?${params}`);
  if (!r.ok) throw new Error("Failed to fetch equity");
  return r.json();
}

export async function fetchModelCard() {
  const r = await fetch(`${API_BASE}/meta`);
  if (!r.ok) throw new Error("Failed to fetch model card");
  return r.json();
}

export async function scoreLatest(
  apiBase: string,
  params: { k: number; liq: number; exclude_pemantauan: boolean },
  files: { features: File; raw?: File; meta?: File }
) {
  const q = new URLSearchParams({
    k: String(params.k),
    liq: String(params.liq),
    exclude_pemantauan: String(params.exclude_pemantauan)
  });
  const fd = new FormData();
  fd.append("features_csv", files.features);
  if (files.raw) fd.append("raw_csv", files.raw);
  if (files.meta) fd.append("meta_xlsx", files.meta);
  const res = await fetch(`${apiBase}/score?${q.toString()}`, {
    method: "POST",
    body: fd
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export function createSSEConnection(onMessage: (data: any) => void) {
  const eventSource = new EventSource(`${API_BASE}/alerts/stream`);
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("Failed to parse SSE message", e);
    }
  };
  return eventSource;
}
