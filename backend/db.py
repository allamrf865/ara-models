import os, json
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
import pandas as pd

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

def save_dataset(
    df: pd.DataFrame,
    source_type: str,
    source_name: str,
    market: str,
    validation_status: str,
    validation_notes: Dict,
    asof_date: Optional[date] = None
) -> str:
    if not supabase:
        raise RuntimeError("Supabase not configured")

    if asof_date is None and "Date" in df.columns:
        asof_date = pd.to_datetime(df["Date"]).max().date()

    data_json = df.to_dict(orient="records")
    for record in data_json:
        if "Date" in record and isinstance(record["Date"], date):
            record["Date"] = record["Date"].isoformat()

    dataset = {
        "market": market,
        "source_type": source_type,
        "source_name": source_name,
        "asof_date": asof_date.isoformat() if asof_date else None,
        "row_count": len(df),
        "ticker_count": df["Ticker"].nunique() if "Ticker" in df.columns else 0,
        "validation_status": validation_status,
        "validation_notes": validation_notes,
        "data": data_json,
        "metadata": {
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    }

    result = supabase.table("datasets").insert(dataset).execute()
    return result.data[0]["id"]

def get_dataset(dataset_id: str) -> Optional[pd.DataFrame]:
    if not supabase:
        return None

    result = supabase.table("datasets").select("*").eq("id", dataset_id).maybeSingle().execute()
    if not result.data:
        return None

    data = result.data["data"]
    df = pd.DataFrame(data)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

def get_latest_dataset(market: str = "ID", source_type: Optional[str] = None) -> Optional[tuple]:
    if not supabase:
        return None

    query = supabase.table("datasets")\
        .select("*")\
        .eq("market", market)\
        .order("created_at", desc=True)\
        .limit(1)

    if source_type:
        query = query.eq("source_type", source_type)

    result = query.execute()

    if not result.data:
        return None

    dataset = result.data[0]
    df = pd.DataFrame(dataset["data"])
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

    return dataset["id"], df, dataset

def get_datasets_by_date(market: str, asof_date: date) -> List[Dict]:
    if not supabase:
        return []

    result = supabase.table("datasets")\
        .select("id, source_type, source_name, created_at, row_count")\
        .eq("market", market)\
        .eq("asof_date", asof_date.isoformat())\
        .order("created_at", desc=True)\
        .execute()

    return result.data

def create_alert_schedule(
    market: str,
    run_at_local: str,
    timezone: str,
    k: int,
    liq: float,
    exclude_pemantauan: bool,
    channels: List[str]
) -> str:
    if not supabase:
        raise RuntimeError("Supabase not configured")

    from calendar_utils import calculate_next_run

    schedule = {
        "market": market,
        "run_at_local": run_at_local,
        "timezone": timezone,
        "k": k,
        "liq": float(liq),
        "exclude_pemantauan": exclude_pemantauan,
        "channels": channels,
        "next_run": calculate_next_run(run_at_local, timezone).isoformat()
    }

    result = supabase.table("alert_schedules").insert(schedule).execute()
    return result.data[0]["id"]

def get_pending_alerts() -> List[Dict]:
    if not supabase:
        return []

    now = datetime.utcnow().isoformat()
    result = supabase.table("alert_schedules")\
        .select("*")\
        .eq("is_active", True)\
        .lte("next_run", now)\
        .execute()

    return result.data

def update_alert_last_run(schedule_id: str, next_run: datetime):
    if not supabase:
        return

    supabase.table("alert_schedules")\
        .update({"last_run": datetime.utcnow().isoformat(), "next_run": next_run.isoformat()})\
        .eq("id", schedule_id)\
        .execute()
