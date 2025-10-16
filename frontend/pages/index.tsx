import { useState } from "react";
import { scoreLatest } from "../lib/api";

export default function Home() {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";
  const [k, setK] = useState(50);
  const [liq, setLiq] = useState(0.5);
  const [excl, setExcl] = useState(true);
  const [features, setFeatures] = useState<File | null>(null);
  const [raw, setRaw] = useState<File | null>(null);
  const [meta, setMeta] = useState<File | null>(null);
  const [out, setOut] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const go = async () => {
    setErr(null);
    if (!API_BASE) { setErr("NEXT_PUBLIC_API_BASE belum diset."); return; }
    if (!features) { setErr("Upload features CSV dulu."); return; }
    setLoading(true);
    try {
      const data = await scoreLatest(API_BASE, { k, liq, exclude_pemantauan: excl }, { features, raw: raw || undefined, meta: meta || undefined });
      setOut(data);
    } catch (e:any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{maxWidth:900, margin:"40px auto", padding:"0 20px", fontFamily:"sans-serif"}}>
      <h1>ARA Candidate Scoring</h1>
      <p>Upload satu hari fitur latest (CSV). Opsional: raw latest [Date,Ticker,Volume] & metadata XLSX.</p>
      <div style={{display:"grid", gap:12, gridTemplateColumns:"1fr 1fr"}}>
        <label>features CSV <input type="file" accept=".csv" onChange={e=>setFeatures(e.target.files?.[0] || null)} /></label>
        <label>raw CSV (optional) <input type="file" accept=".csv" onChange={e=>setRaw(e.target.files?.[0] || null)} /></label>
        <label>meta XLSX (optional) <input type="file" accept=".xlsx" onChange={e=>setMeta(e.target.files?.[0] || null)} /></label>
        <label>Top-K <input type="number" value={k} min={1} max={200} onChange={e=>setK(parseInt(e.target.value||"50"))} /></label>
        <label>Liquidity floor (vol_rank_day) <input type="number" step="0.05" min={0} max={1} value={liq} onChange={e=>setLiq(parseFloat(e.target.value||"0.5"))} /></label>
        <label><input type="checkbox" checked={excl} onChange={e=>setExcl(e.target.checked)} /> Exclude “Pemantauan Khusus”</label>
      </div>
      <div style={{marginTop:16}}>
        <button onClick={go} disabled={loading} style={{padding:"10px 18px"}}>{loading ? "Scoring..." : "Run Scoring"}</button>
      </div>
      {err && <pre style={{color:"crimson", whiteSpace:"pre-wrap"}}>{err}</pre>}
      {out && (
        <>
          <h3 style={{marginTop:24}}>Result (latest_date {out.latest_date})</h3>
          <p>Rows scored: {out.rows_scored}</p>
          <h4>Top Screened</h4>
          <table style={{width:"100%", borderCollapse:"collapse"}}>
            <thead><tr><th style={{textAlign:"left"}}>Ticker</th><th>Proba</th><th>vol_rank_day</th><th>Papan</th></tr></thead>
            <tbody>
              {out.top_screened.map((r:any, i:number)=>(
                <tr key={i}>
                  <td style={{padding:"6px 4px"}}>{r.Ticker || "-"}</td>
                  <td style={{textAlign:"right"}}>{(r.proba_ARA_t1 ?? 0).toFixed(4)}</td>
                  <td style={{textAlign:"right"}}>{r.vol_rank_day!=null ? r.vol_rank_day.toFixed(3) : "-"}</td>
                  <td style={{textTransform:"capitalize"}}>{r.Papan || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <details style={{marginTop:8}}>
            <summary>Top All (tanpa screening)</summary>
            <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(out.top_all.slice(0,50), null, 2)}</pre>
          </details>
        </>
      )}
      <footer style={{marginTop:40, opacity:0.7}}>API base: {API_BASE}</footer>
    </main>
  );
}
