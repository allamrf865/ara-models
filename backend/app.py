import os, io, json, pandas as pd, numpy as np
from fastapi import FastAPI, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse
from model_loader import download_bundle, load_bundle_flex
from utils import predict_mean, enrich_vol_rank, screen

GITHUB_REPO = os.getenv("GITHUB_REPO", "allamrf865/ara-models")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ARTIFACT_TAG = os.getenv("ARTIFACT_TAG", "")
ARTIFACT_ZIP_URL = os.getenv("ARTIFACT_ZIP_URL", "")

EXTRACT_DIR, MODEL_CARD, CALIB, MODELS, FEAT_FROM_BUNDLE = load_bundle_flex(
    download_bundle(GITHUB_REPO, token=GITHUB_TOKEN or None,
                    tag=ARTIFACT_TAG or None,
                    direct_url=ARTIFACT_ZIP_URL or None)
)

app = FastAPI(title="ARA Rank API", version="1.0.0")

@app.get("/health")
def health():
    return {
        "ok": True,
        "models": len(MODELS),
        "has_calibrator": CALIB is not None,
        "features_from_bundle": FEAT_FROM_BUNDLE is not None
    }

@app.get("/meta")
def meta():
    return {
        "card": MODEL_CARD,
        "required_features_count": len(FEAT_FROM_BUNDLE) if FEAT_FROM_BUNDLE else None,
        "required_features_sample": FEAT_FROM_BUNDLE[:10] if FEAT_FROM_BUNDLE else None
    }

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

    return {
        "latest_date": str(latest_date.date()),
        "rows_scored": int(len(out_all)),
        "top_all": top_all.to_dict(orient="records"),
        "top_screened": top_scr.to_dict(orient="records"),
        "screening": {"exclude_pemantauan": exclude_pemantauan, "liq_floor": liq}
    }
