import io, os, re, json
import pandas as pd
import numpy as np
from datetime import datetime, date
import pytz
from typing import Dict, List, Tuple, Any
import pdfplumber
from PIL import Image
import pytesseract
from docx import Document
from faster_whisper import WhisperModel
import yfinance as yf

REQUIRED_COLS = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]
OPTIONAL_COLS = ["AdjClose", "Papan", "limit_price_t", "limit_pct_t"]
MAX_FILE_SIZE = 50 * 1024 * 1024

def normalize_ticker(ticker: str, market: str = "ID") -> str:
    ticker = str(ticker).strip().upper()
    if market == "ID" and not ticker.endswith(".JK"):
        ticker = f"{ticker}.JK"
    return ticker

def normalize_timezone(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        if df["Date"].dt.tz is not None:
            df["Date"] = df["Date"].dt.tz_convert("UTC").dt.tz_localize(None)
        df["Date"] = df["Date"].dt.date
    return df

def validate_dataset(df: pd.DataFrame) -> Tuple[str, Dict]:
    notes = {"errors": [], "warnings": [], "info": []}

    if df.empty:
        notes["errors"].append("Dataset is empty")
        return "error", notes

    missing_required = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_required:
        notes["errors"].append(f"Missing required columns: {missing_required}")
        return "error", notes

    null_counts = df[REQUIRED_COLS].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            pct = (count / len(df)) * 100
            if col in ["Date", "Ticker"]:
                notes["errors"].append(f"{col} has {count} null values ({pct:.1f}%)")
            else:
                notes["warnings"].append(f"{col} has {count} null values ({pct:.1f}%)")

    if "errors" in notes and notes["errors"]:
        return "error", notes

    df_clean = df.dropna(subset=["Date", "Ticker"])
    dupes = df_clean.duplicated(subset=["Date", "Ticker"], keep="first").sum()
    if dupes > 0:
        notes["warnings"].append(f"Found {dupes} duplicate (Date, Ticker) pairs - keeping first occurrence")

    date_range = f"{df_clean['Date'].min()} to {df_clean['Date'].max()}"
    ticker_count = df_clean["Ticker"].nunique()
    notes["info"].append(f"Date range: {date_range}")
    notes["info"].append(f"Unique tickers: {ticker_count}")
    notes["info"].append(f"Total rows: {len(df_clean)}")

    status = "warning" if notes["warnings"] else "valid"
    return status, notes

def ingest_csv(file_bytes: bytes, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df = normalize_timezone(df)
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].apply(lambda x: normalize_ticker(x, market))
    return df, "csv"

def ingest_excel(file_bytes: bytes, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    df = pd.read_excel(io.BytesIO(file_bytes))
    df = normalize_timezone(df)
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].apply(lambda x: normalize_ticker(x, market))
    return df, "excel"

def ingest_pdf(file_bytes: bytes, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    tables = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables()
            for table in extracted:
                if table and len(table) > 1:
                    tables.append(table)

    if not tables:
        raise ValueError("No tables found in PDF")

    table_data = tables[0]
    df = pd.DataFrame(table_data[1:], columns=table_data[0])
    df = normalize_timezone(df)
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].apply(lambda x: normalize_ticker(x, market))
    return df, "pdf"

def ingest_image(file_bytes: bytes, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) < 2:
        raise ValueError("Could not extract enough data from image")

    data = []
    for line in lines[1:]:
        parts = re.split(r"[\s,\t]+", line)
        if len(parts) >= 6:
            data.append(parts[:7])

    if not data:
        raise ValueError("No valid data rows found in image")

    headers = re.split(r"[\s,\t]+", lines[0])
    df = pd.DataFrame(data, columns=headers[:len(data[0])])
    df = normalize_timezone(df)
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].apply(lambda x: normalize_ticker(x, market))
    return df, "image"

def ingest_docx(file_bytes: bytes, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    doc = Document(io.BytesIO(file_bytes))
    tables_data = []

    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        if len(table_data) > 1:
            tables_data.append(table_data)

    if not tables_data:
        raise ValueError("No tables found in DOCX")

    table = tables_data[0]
    df = pd.DataFrame(table[1:], columns=table[0])
    df = normalize_timezone(df)
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].apply(lambda x: normalize_ticker(x, market))
    return df, "docx"

def ingest_paste(text: str, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    delimiter = "\t" if "\t" in text else "," if "," in text else None

    if delimiter:
        df = pd.read_csv(io.StringIO(text), sep=delimiter)
    else:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        data = [re.split(r"\s+", line) for line in lines]
        df = pd.DataFrame(data[1:], columns=data[0])

    df = normalize_timezone(df)
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].apply(lambda x: normalize_ticker(x, market))
    return df, "paste"

def ingest_scrape(source: str, market: str = "ID", tickers: List[str] = None) -> Tuple[pd.DataFrame, str]:
    if source.lower() == "yahoo":
        if not tickers:
            raise ValueError("Tickers required for Yahoo scraping")

        data_frames = []
        for ticker in tickers:
            try:
                normalized = normalize_ticker(ticker, market)
                stock = yf.Ticker(normalized)
                hist = stock.history(period="5d")
                if not hist.empty:
                    hist["Ticker"] = normalized
                    hist["Date"] = hist.index.date
                    data_frames.append(hist.reset_index(drop=True))
            except Exception as e:
                continue

        if not data_frames:
            raise ValueError("No data retrieved from Yahoo Finance")

        df = pd.concat(data_frames, ignore_index=True)
        df = df[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]]
        df["AdjClose"] = df["Close"]
        return df, "scrape_yahoo"

    raise ValueError(f"Unsupported scrape source: {source}")

def ingest_audio(file_bytes: bytes, market: str = "ID") -> Tuple[pd.DataFrame, str]:
    audio_path = f"/tmp/audio_{datetime.now().timestamp()}.wav"
    with open(audio_path, "wb") as f:
        f.write(file_bytes)

    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, language="id")
        text = " ".join([seg.text for seg in segments])
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

    ticker_pattern = r"\b[A-Z]{4}\b"
    tickers = re.findall(ticker_pattern, text)

    if not tickers:
        raise ValueError("No tickers detected in audio transcription")

    data = []
    for ticker in set(tickers):
        data.append({
            "Ticker": normalize_ticker(ticker, market),
            "Date": date.today(),
            "Open": 0, "High": 0, "Low": 0, "Close": 0, "Volume": 0
        })

    df = pd.DataFrame(data)
    return df, "audio"
