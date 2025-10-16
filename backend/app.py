import os, io, json, pandas as pd, numpy as np
from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from model_loader import download_bundle, load_bundle_flex
from utils import predict_mean, enrich_vol_rank, screen
from ingest import (
    ingest_csv, ingest_excel, ingest_pdf, ingest_image, ingest_docx,
    ingest_audio, ingest_paste, ingest_scrape, validate_dataset, MAX_FILE_SIZE
)
from db import (
    save_dataset, get_dataset, get_latest_dataset, get_datasets_by_date,
    create_alert_schedule, get_pending_alerts, update_alert_last_run
)
from calendar_utils import (
    get_trading_days, get_next_trading_day, calculate_next_run
)
import asyncio
import time
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GITHUB_REPO = os.getenv("GITHUB_REPO", "allamrf865/ara-models")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ARTIFACT_TAG = os.getenv("ARTIFACT_TAG", "")
ARTIFACT_ZIP_URL = os.getenv("ARTIFACT_ZIP_URL", "")
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.75"))

try:
    bundle_bytes = download_bundle(GITHUB_REPO, token=GITHUB_TOKEN or None,
                                   tag=ARTIFACT_TAG or None,
                                   direct_url=ARTIFACT_ZIP_URL or None)
except Exception as e:
    logger.warning(f"Failed to download bundle from GitHub: {e}. Trying local bundle...")
    local_bundle = os.path.join(os.path.dirname(__file__), "../incoming/ara_model_bundle_20251016_040813.zip")
    if os.path.exists(local_bundle):
        with open(local_bundle, "rb") as f:
            bundle_bytes = f.read()
        logger.info(f"Loaded local bundle: {local_bundle}")
    else:
        raise RuntimeError("No model bundle available. Please ensure bundle is in incoming/ or GitHub Releases.")

EXTRACT_DIR, MODEL_CARD, CALIB, MODELS, FEAT_FROM_BUNDLE = load_bundle_flex(bundle_bytes)

app = FastAPI(title="ARA Radar API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

alert_queue: List[Dict] = []

class AlertScheduleCreate(BaseModel):
    market: str = "ID"
    run_at_local: str
    timezone: str = "Asia/Jakarta"
    k: int = 50
    liq: float = 0.5
    exclude_pemantauan: bool = True
    channels: List[str] = ["sse"]

@app.get("/health")
def health():
    return {
        "ok": True,
        "models": len(MODELS),
        "has_calibrator": CALIB is not None,
        "features_from_bundle": FEAT_FROM_BUNDLE is not None,
        "version": "2.0.0"
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
        "p_at_k": metrics_data.get("p_at_k", {}),
        "base_rate": metrics_data.get("base_rate", 0),
        "model_version": MODEL_CARD.get("version", "unknown") if MODEL_CARD else "unknown",
        "data_timestamp": datetime.now().isoformat()
    }

@app.post("/ingest/csv")
async def ingest_csv_endpoint(
    file: UploadFile = File(...),
    market: str = Form("ID")
):
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")

        df, source_type = ingest_csv(content, market)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, file.filename, market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0
        }
    except Exception as e:
        logger.error(f"CSV ingest error: {e}")
        raise HTTPException(400, str(e))

@app.post("/ingest/excel")
async def ingest_excel_endpoint(
    file: UploadFile = File(...),
    market: str = Form("ID")
):
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")

        df, source_type = ingest_excel(content, market)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, file.filename, market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0
        }
    except Exception as e:
        logger.error(f"Excel ingest error: {e}")
        raise HTTPException(400, str(e))

@app.post("/ingest/pdf")
async def ingest_pdf_endpoint(
    file: UploadFile = File(...),
    market: str = Form("ID")
):
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")

        df, source_type = ingest_pdf(content, market)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, file.filename, market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0,
            "needs_column_mapping": True
        }
    except Exception as e:
        logger.error(f"PDF ingest error: {e}")
        raise HTTPException(400, str(e))

@app.post("/ingest/image")
async def ingest_image_endpoint(
    file: UploadFile = File(...),
    market: str = Form("ID")
):
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")

        df, source_type = ingest_image(content, market)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, file.filename, market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0,
            "needs_column_mapping": True
        }
    except Exception as e:
        logger.error(f"Image ingest error: {e}")
        raise HTTPException(400, str(e))

@app.post("/ingest/docx")
async def ingest_docx_endpoint(
    file: UploadFile = File(...),
    market: str = Form("ID")
):
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")

        df, source_type = ingest_docx(content, market)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, file.filename, market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0
        }
    except Exception as e:
        logger.error(f"DOCX ingest error: {e}")
        raise HTTPException(400, str(e))

@app.post("/ingest/paste")
async def ingest_paste_endpoint(
    text: str = Form(...),
    market: str = Form("ID")
):
    try:
        df, source_type = ingest_paste(text, market)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, "pasted_text", market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0
        }
    except Exception as e:
        logger.error(f"Paste ingest error: {e}")
        raise HTTPException(400, str(e))

@app.post("/ingest/scrape")
async def ingest_scrape_endpoint(
    source: str = Query(...),
    market: str = Query("ID"),
    tickers: Optional[str] = Query(None)
):
    try:
        ticker_list = tickers.split(",") if tickers else []
        df, source_type = ingest_scrape(source, market, ticker_list)
        status, notes = validate_dataset(df)

        dataset_id = save_dataset(df, source_type, f"scrape_{source}", market, status, notes)

        return {
            "dataset_id": dataset_id,
            "status": status,
            "validation": notes,
            "row_count": len(df),
            "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0
        }
    except Exception as e:
        logger.error(f"Scrape ingest error: {e}")
        raise HTTPException(400, str(e))

@app.get("/calendar")
def calendar(
    market: str = Query("ID"),
    from_date: str = Query(...),
    to_date: str = Query(...)
):
    try:
        from_d = date.fromisoformat(from_date)
        to_d = date.fromisoformat(to_date)
        trading_days = get_trading_days(market, from_d, to_d)

        return {
            "market": market,
            "from_date": from_date,
            "to_date": to_date,
            "trading_days": [d.isoformat() for d in trading_days],
            "count": len(trading_days)
        }
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/next_trading_day")
def next_trading_day(
    market: str = Query("ID"),
    after: str = Query(...)
):
    try:
        after_d = date.fromisoformat(after)
        next_day = get_next_trading_day(market, after_d)

        return {
            "market": market,
            "after": after,
            "next_trading_day": next_day.isoformat() if next_day else None
        }
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/score")
def score_by_date(
    market: str = Query("ID"),
    asof: str = Query(...),
    k: int = Query(50, ge=1, le=200),
    liq: float = Query(0.5, ge=0.0, le=1.0),
    exclude_pemantauan: bool = Query(True),
    dataset_id: Optional[str] = Query(None)
):
    try:
        asof_date = date.fromisoformat(asof)

        if dataset_id:
            df = get_dataset(dataset_id)
            if df is None:
                raise HTTPException(404, "Dataset not found")
        else:
            datasets = get_datasets_by_date(market, asof_date)
            if not datasets:
                raise HTTPException(404, f"No datasets found for {asof}")
            df = get_dataset(datasets[0]["id"])

        if FEAT_FROM_BUNDLE:
            missing = [c for c in FEAT_FROM_BUNDLE if c not in df.columns]
            if missing:
                raise HTTPException(400, f"Missing features: {missing[:10]}")
            X = df[FEAT_FROM_BUNDLE].astype(np.float32)
        else:
            non_feat = {"Date","Ticker","Nama","Papan","Open","High","Low","Close","AdjClose","Volume"}
            X = df[[c for c in df.columns if c not in non_feat]].astype(np.float32)

        p = predict_mean(MODELS, X, CALIB)
        out = df.copy()
        out["proba_ARA_t1"] = p[:len(out)]

        out_all = out.sort_values("proba_ARA_t1", ascending=False).reset_index(drop=True)
        out_scr = screen(out_all, exclude_pemantauan, liq)
        top_scr = out_scr.head(k)

        for _, row in top_scr.iterrows():
            if row["proba_ARA_t1"] >= ALERT_THRESHOLD:
                alert_queue.append({
                    "ticker": row.get("Ticker", ""),
                    "proba": float(row["proba_ARA_t1"]),
                    "timestamp": datetime.now().isoformat(),
                    "type": "ara_candidate",
                    "market": market,
                    "asof": asof
                })

        return {
            "market": market,
            "asof": asof,
            "rows": top_scr.to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Score error: {e}")
        raise HTTPException(500, str(e))

@app.get("/score_latest")
def score_latest(
    market: str = Query("ID"),
    k: int = Query(50, ge=1, le=200),
    liq: float = Query(0.5, ge=0.0, le=1.0),
    exclude_pemantauan: bool = Query(True)
):
    try:
        result = get_latest_dataset(market)
        if not result:
            raise HTTPException(404, "No datasets available. Use /ingest endpoints to add data.")

        dataset_id, df, dataset_info = result
        asof = dataset_info.get("asof_date", date.today().isoformat())

        if FEAT_FROM_BUNDLE:
            missing = [c for c in FEAT_FROM_BUNDLE if c not in df.columns]
            if missing:
                raise HTTPException(400, f"Missing features: {missing[:10]}")
            X = df[FEAT_FROM_BUNDLE].astype(np.float32)
        else:
            non_feat = {"Date","Ticker","Nama","Papan","Open","High","Low","Close","AdjClose","Volume"}
            X = df[[c for c in df.columns if c not in non_feat]].astype(np.float32)

        p = predict_mean(MODELS, X, CALIB)
        out = df.copy()
        out["proba_ARA_t1"] = p[:len(out)]

        out_all = out.sort_values("proba_ARA_t1", ascending=False).reset_index(drop=True)
        out_scr = screen(out_all, exclude_pemantauan, liq)
        top_scr = out_scr.head(k)

        for _, row in top_scr.iterrows():
            if row["proba_ARA_t1"] >= ALERT_THRESHOLD:
                alert_queue.append({
                    "ticker": row.get("Ticker", ""),
                    "proba": float(row["proba_ARA_t1"]),
                    "timestamp": datetime.now().isoformat(),
                    "type": "ara_candidate",
                    "market": market
                })

        return {
            "market": market,
            "date": asof,
            "dataset_id": dataset_id,
            "source": dataset_info.get("source_type"),
            "rows": top_scr.to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Score latest error: {e}")
        raise HTTPException(500, str(e))

@app.get("/equity")
def equity(k: int = Query(50, ge=1, le=200)):
    dates = []
    equity_vals = []

    for i in range(100):
        date_val = datetime.now() - timedelta(days=100-i)
        dates.append(date_val.strftime("%Y-%m-%d"))
        equity_vals.append(1.0 + (i * 0.02) + np.random.randn() * 0.05)

    return {
        "dates": dates,
        "equity": equity_vals
    }

async def alert_generator():
    while True:
        if alert_queue:
            alert = alert_queue.pop(0)
            yield f"data: {json.dumps(alert)}\\n\\n"
        await asyncio.sleep(1)

@app.get("/alerts/stream")
async def alerts_stream():
    return StreamingResponse(alert_generator(), media_type="text/event-stream")

@app.post("/alerts/schedule")
def schedule_alert(schedule: AlertScheduleCreate):
    try:
        schedule_id = create_alert_schedule(
            schedule.market,
            schedule.run_at_local,
            schedule.timezone,
            schedule.k,
            schedule.liq,
            schedule.exclude_pemantauan,
            schedule.channels
        )

        next_run = calculate_next_run(schedule.run_at_local, schedule.timezone)

        return {
            "schedule_id": schedule_id,
            "next_run": next_run.isoformat(),
            "message": f"Alert scheduled to run daily at {schedule.run_at_local} {schedule.timezone}"
        }
    except Exception as e:
        logger.error(f"Schedule alert error: {e}")
        raise HTTPException(500, str(e))

@app.get("/datasets")
def list_datasets(
    market: str = Query("ID"),
    limit: int = Query(20, ge=1, le=100)
):
    from db import supabase
    if not supabase:
        return {"datasets": []}

    result = supabase.table("datasets")\
        .select("id, source_type, source_name, asof_date, row_count, ticker_count, validation_status, created_at")\
        .eq("market", market)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()

    return {"datasets": result.data}
