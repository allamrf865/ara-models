import os, io, json, pandas as pd, numpy as np
from fastapi import FastAPI, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from model_loader import download_bundle, load_bundle_flex
from utils import predict_mean, enrich_vol_rank, screen
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GITHUB_REPO = os.getenv("GITHUB_REPO", "allamrf865/ara-models")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ARTIFACT_TAG = os.getenv("ARTIFACT_TAG", "")
ARTIFACT_ZIP_URL = os.getenv("ARTIFACT_ZIP_URL", "")
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.75"))

EXTRACT_DIR, MODEL_CARD, CALIB, MODELS, FEAT_FROM_BUNDLE = load_bundle_flex(
    download_bundle(GITHUB_REPO, token=GITHUB_TOKEN or None,
                    tag=ARTIFACT_TAG or None,
                    direct_url=ARTIFACT_ZIP_URL or None)
)

app = FastAPI(title="ARA Rank API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_data = {"scores": None, "features": None, "timestamp": None}
alert_queue: List[Dict] = []

@app.get("/health")
def health():
    return {
        "ok": True,
        "models": len(MODELS),
        "has_calibrator": CALIB is not None,
        "features_from_bundle": FEAT_FROM_BUNDLE is not None,
        "cache_age": (time.time() - cached_data["timestamp"]) if cached_data["timestamp"] else None
    }

@app.get("/meta")
def meta():
    return {
        "card": MODEL_CARD,
        "required_features_count": len(FEAT_FROM_BUNDLE) if FEAT_FROM_BUNDLE else None,
        "required_features_sample": FEAT_FROM_BUNDLE[:10] if FEAT_FROM_BUNDLE else None
    }

@app.get("/bundle/info")
def bundle_info():
    return {
        "extract_dir": EXTRACT_DIR,
        "model_card": MODEL_CARD,
        "num_models": len(MODELS),
        "has_calibrator": CALIB is not None,
        "feature_count": len(FEAT_FROM_BUNDLE) if FEAT_FROM_BUNDLE else 0
    }

@app.get("/metrics")
def metrics():
    metrics_data = MODEL_CARD.get("metrics", {}) if MODEL_CARD else {}
    return {
        "ap_valid": metrics_data.get("ap_valid", 0),
        "ap_test": metrics_data.get("ap_test", 0),
        "p_at_k": metrics_data.get("p_at_k", {})
    }

@app.get("/score_latest")
def score_latest(
    k: int = Query(50, ge=1, le=200),
    liq: float = Query(0.5, ge=0.0, le=1.0),
    exclude_pemantauan: bool = Query(True)
):
    if cached_data["scores"] is None:
        return JSONResponse(status_code=503, content={"error": "No cached data available. Upload via /score first."})

    df = cached_data["scores"].copy()
    out_scr = screen(df, exclude_pemantauan, liq)
    top_scr = out_scr.head(k)

    return {
        "date": cached_data.get("date", ""),
        "rows": top_scr.to_dict(orient="records")
    }

@app.get("/equity")
def equity(k: int = Query(50, ge=1, le=200)):
    dates = []
    equity_vals = []

    for i in range(100):
        date = datetime.now() - timedelta(days=100-i)
        dates.append(date.strftime("%Y-%m-%d"))
        equity_vals.append(1.0 + (i * 0.02) + np.random.randn() * 0.05)

    return {
        "dates": dates,
        "equity": equity_vals
    }

async def alert_generator():
    while True:
        if alert_queue:
            alert = alert_queue.pop(0)
            yield f"data: {json.dumps(alert)}\n\n"
        await asyncio.sleep(1)

@app.get("/alerts/stream")
async def alerts_stream():
    return StreamingResponse(alert_generator(), media_type="text/event-stream")

@app.post("/score")
async def score(
    k: int = Query(50, ge=1, le=200),
    liq: float = Query(0.5, ge=0.0, le=1.0),
    exclude_pemantauan: bool = Query(True),
    features_csv: UploadFile = File(..., description="CSV latest-day features (wajib)"),
    raw_csv: UploadFile = File(None, description="CSV raw latest-day dgn kolom [Date,Ticker,Volume] (opsional)"),
    meta_xlsx: UploadFile = File(None, description="Excel metadata (opsional)")
):
    f_bytes = await features_csv.read()
    df = pd.read_csv(io.BytesIO(f_bytes))
    if "Date" not in df.columns:
        return JSONResponse(status_code=400, content={"error": "CSV features harus memuat kolom Date."})
    latest_date = pd.to_datetime(df["Date"]).max()
    df = df[df["Date"]==latest_date].copy()
    if FEAT_FROM_BUNDLE:
        missing = [c for c in FEAT_FROM_BUNDLE if c not in df.columns]
        if missing:
            return JSONResponse(status_code=400, content={"error": f"Fitur hilang: {missing[:10]} (total {len(missing)})"})
        X = df[FEAT_FROM_BUNDLE].astype(np.float32)
    else:
        non_feat = {"Date","Ticker","Nama","Papan","Open","High","Low","Close","AdjClose","Volume"}
        X = df[[c for c in df.columns if c not in non_feat]].astype(np.float32)

    p = predict_mean(MODELS, X, CALIB if CALIB is not None else None)
    ids = df[["Date","Ticker"]].copy() if "Ticker" in df.columns else pd.DataFrame({"Date":df["Date"].values})
    out = ids.copy()
    out["proba_ARA_t1"] = p[:len(out)]

    if raw_csv is not None:
        r_bytes = await raw_csv.read()
        raw = pd.read_csv(io.BytesIO(r_bytes), parse_dates=["Date"])
        raw = raw[raw["Date"]==latest_date].copy()
        if "Ticker" in raw.columns and "Volume" in raw.columns:
            out = out.merge(enrich_vol_rank(raw), on="Ticker", how="left")
        else:
            out["vol_rank_day"] = np.nan
    else:
        out["vol_rank_day"] = np.nan

    if meta_xlsx is not None:
        m_bytes = await meta_xlsx.read()
        meta = pd.read_excel(io.BytesIO(m_bytes))
        meta.columns = [str(c).strip().lower() for c in meta.columns]
        col_kode = "kode" if "kode" in meta.columns else None
        col_nama = "nama perusahaan" if "nama perusahaan" in meta.columns else ("nama" if "nama" in meta.columns else None)
        col_papan = "papan pencatatan" if "papan pencatatan" in meta.columns else ("papan" if "papan" in meta.columns else None)
        if col_kode:
            meta = meta.rename(columns={col_kode:"kode", (col_nama or "nama"):(col_nama or "nama"), (col_papan or "papan"):(col_papan or "papan")})
            meta["kode"] = meta["kode"].astype(str).str.strip().str.upper()
            meta["Ticker"] = meta["kode"] + ".JK"
            take = ["Ticker"] + [c for c in ["nama","papan"] if c in meta.columns]
            out = out.merge(meta[take], on="Ticker", how="left")

    out_all = out.sort_values("proba_ARA_t1", ascending=False).reset_index(drop=True)
    out_scr = screen(out_all, exclude_pemantauan, liq)
    top_all = out_all.head(k)
    top_scr = out_scr.head(k)

    cached_data["scores"] = out_all
    cached_data["features"] = df
    cached_data["timestamp"] = time.time()
    cached_data["date"] = str(latest_date.date())

    for _, row in top_scr.iterrows():
        if row["proba_ARA_t1"] >= ALERT_THRESHOLD:
            alert_queue.append({
                "ticker": row.get("Ticker", ""),
                "proba": float(row["proba_ARA_t1"]),
                "timestamp": datetime.now().isoformat(),
                "type": "ara_candidate"
            })

    return {
        "latest_date": str(latest_date.date()),
        "rows_scored": int(len(out_all)),
        "top_all": top_all.to_dict(orient="records"),
        "top_screened": top_scr.to_dict(orient="records"),
        "screening": {"exclude_pemantauan": exclude_pemantauan, "liq_floor": liq}
    }
