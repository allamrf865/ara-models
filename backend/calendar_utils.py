from datetime import date, datetime, timedelta
from typing import List, Optional
import pytz
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5

def get_trading_days(market: str, from_date: date, to_date: date) -> List[date]:
    if not supabase:
        trading_days = []
        current = from_date
        while current <= to_date:
            if not is_weekend(current):
                trading_days.append(current)
            current += timedelta(days=1)
        return trading_days

    try:
        result = supabase.table("trading_calendar")\
            .select("date, is_trading_day")\
            .eq("market", market)\
            .gte("date", from_date.isoformat())\
            .lte("date", to_date.isoformat())\
            .execute()

        holidays = {row["date"] for row in result.data if not row["is_trading_day"]}
    except Exception as e:
        holidays = set()

    trading_days = []
    current = from_date
    while current <= to_date:
        date_str = current.isoformat()
        if not is_weekend(current) and date_str not in holidays:
            trading_days.append(current)
        current += timedelta(days=1)

    return trading_days

def get_next_trading_day(market: str, after: date) -> Optional[date]:
    trading_days = get_trading_days(market, after + timedelta(days=1), after + timedelta(days=30))
    return trading_days[0] if trading_days else None

def get_prev_trading_day(market: str, before: date) -> Optional[date]:
    trading_days = get_trading_days(market, before - timedelta(days=30), before - timedelta(days=1))
    return trading_days[-1] if trading_days else None

def get_market_close_time(market: str) -> str:
    close_times = {
        "ID": "16:00",
        "US": "16:00",
    }
    return close_times.get(market, "16:00")

def calculate_next_run(run_at_local: str, timezone_str: str) -> datetime:
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    hour, minute = map(int, run_at_local.split(":"))

    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)

    return next_run.astimezone(pytz.UTC).replace(tzinfo=None)
