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
