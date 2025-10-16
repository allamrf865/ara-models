# ARA Radar v2.0 - End-to-End Stock Ranking System

Complete machine learning-powered stock ranking system with multi-source data ingestion, real-time alerts, and calendar-aware scheduling.

## Overview

ARA Radar v2.0 is an advanced stock market analysis platform that:
- **Ingests** data from 8+ sources (CSV, Excel, PDF, Images, DOCX, Audio, Paste, API scraping)
- **Validates & normalizes** all data to EOD schema with timezone/ticker handling
- **Scores** stocks using XGBoost ensemble + isotonic calibration
- **Alerts** via SSE streams, Web Push, and scheduled runs
- **Tracks** trading calendars and respects market holidays

## Key Features

### 🔥 Multi-Source Data Ingestion
Upload or fetch data from:
- **Files**: CSV, Excel, PDF (with OCR), Word DOCX, Images (OCR)
- **Text**: Paste delimited data, auto-detect format
- **APIs**: Yahoo Finance, AlphaVantage (coming soon), EODHD (coming soon)
- **Audio**: Whisper transcription for verbal ticker input (coming soon)

### ✅ Automatic Validation
- Timezone normalization (WIB → UTC)
- Canonical ticker formatting (.JK for Indonesia)
- Duplicate detection & removal
- Missing value handling
- Schema compliance checks

### 📊 Smart Scoring
- XGBoost ensemble models from GitHub Releases
- Isotonic calibration for probability outputs
- Historical & latest data scoring
- Configurable thresholds & filters

### 📅 Calendar-Aware
- Trading day calendars per market
- Holiday exclusions (Indonesia 2025 pre-loaded)
- Next/previous trading day lookups
- Scheduled alerts after market close

### 🔔 Real-Time Alerts
- Server-Sent Events (SSE) streaming
- Web Push notifications
- Scheduled alerts (daily at specific times)
- Multi-channel support

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Frontend      │      │    Backend       │      │   Supabase DB   │
│   Next.js 14    │◄────►│    FastAPI       │◄────►│   PostgreSQL    │
│   + Three.js    │      │    + XGBoost     │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
        │                         │
        │                         │
        ▼                         ▼
   ┌─────────┐             ┌──────────────┐
   │ Netlify │             │ GitHub       │
   │ (CDN)   │             │ Releases     │
   └─────────┘             └──────────────┘
```

## API Endpoints

### Ingestion
- `POST /ingest/csv` - CSV file upload
- `POST /ingest/excel` - Excel file upload
- `POST /ingest/pdf` - PDF table extraction
- `POST /ingest/image` - OCR from images
- `POST /ingest/docx` - Word document tables
- `POST /ingest/audio` - Audio transcription
- `POST /ingest/paste` - Parse pasted text
- `POST /ingest/scrape?source=yahoo&tickers=...` - API scraping

### Scoring
- `GET /score_latest?market=ID&k=50&liq=0.5` - Score latest data
- `GET /score?market=ID&asof=2025-10-15&k=50` - Score by date
- `GET /metrics` - Model performance metrics
- `GET /equity?k=50` - Backtest equity curve

### Calendar
- `GET /calendar?market=ID&from_date=...&to_date=...` - Trading days
- `GET /next_trading_day?market=ID&after=...` - Next trading day

### Alerts
- `GET /alerts/stream` - SSE real-time stream
- `POST /alerts/schedule` - Schedule daily alerts

### Management
- `GET /datasets?market=ID&limit=20` - List ingested datasets
- `GET /health` - Health check
- `GET /bundle/info` - Model bundle info

## Database Schema (Supabase)

### `datasets` Table
Stores all ingested data with validation status and provenance.

```sql
id, user_id, market, source_type, source_name,
ingest_date, asof_date, row_count, ticker_count,
validation_status, validation_notes (jsonb),
data (jsonb), metadata (jsonb)
```

### `alert_schedules` Table
Manages scheduled alert jobs.

```sql
id, market, run_at_local (time), timezone,
k, liq, exclude_pemantauan, channels (jsonb),
is_active, last_run, next_run
```

### `trading_calendar` Table
Tracks trading days and holidays per market.

```sql
id, market, date, is_trading_day, notes
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account (free tier works)
- Render/Fly.io account (backend)
- Netlify account (frontend)

### 1. Clone Repository
```bash
git clone https://github.com/allamrf865/ara-models.git
cd ara-models
```

### 2. Setup Supabase
1. Create project at https://supabase.com
2. Get your project URL and anon key
3. Run the migration (already applied via MCP)

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Supabase credentials

uvicorn app:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install

cp .env.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
# NEXT_PUBLIC_SUPABASE_URL=...
# NEXT_PUBLIC_SUPABASE_ANON_KEY=...

npm run dev
```

Visit http://localhost:8888

### 5. Production Deployment

**Backend (Render)**:
1. Connect GitHub repo
2. Select `backend` directory
3. Set environment variables
4. Deploy

**Frontend (Netlify)**:
1. Connect GitHub repo
2. Build command: `cd frontend && npm install && npm run build`
3. Publish directory: `frontend/.next`
4. Set environment variables
5. Deploy

## Usage Examples

### 1. Ingest CSV Data
```bash
curl -X POST "http://localhost:8000/ingest/csv" \
  -F "file=@stocks.csv" \
  -F "market=ID"
```

Response:
```json
{
  "dataset_id": "uuid-here",
  "status": "valid",
  "validation": {"errors": [], "warnings": [], "info": [...]},
  "row_count": 100,
  "ticker_count": 50
}
```

### 2. Auto-Fetch from Yahoo Finance
```bash
curl -X POST "http://localhost:8000/ingest/scrape?source=yahoo&market=ID&tickers=BBCA,BBRI,TLKM"
```

### 3. Score Latest Data
```bash
curl "http://localhost:8000/score_latest?market=ID&k=50&liq=0.5&exclude_pemantauan=true"
```

Response:
```json
{
  "market": "ID",
  "date": "2025-10-16",
  "dataset_id": "uuid-here",
  "source": "scrape_yahoo",
  "rows": [
    {
      "Ticker": "BBCA.JK",
      "proba_ARA_t1": 0.8542,
      "Papan": "Utama",
      "vol_rank_day": 0.92
    },
    ...
  ]
}
```

### 4. Schedule Daily Alert
```bash
curl -X POST "http://localhost:8000/alerts/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "market": "ID",
    "run_at_local": "16:30",
    "timezone": "Asia/Jakarta",
    "k": 50,
    "liq": 0.5,
    "exclude_pemantauan": true,
    "channels": ["sse"]
  }'
```

## Data Format

### EOD Schema (Normalized)
All ingested data is normalized to this schema:

```
Required:
- Date (date): Trading date
- Ticker (string): Stock ticker (.JK for Indonesia)
- Open (float): Opening price
- High (float): High price
- Low (float): Low price
- Close (float): Closing price
- Volume (int): Trading volume

Optional:
- AdjClose (float): Adjusted closing price
- Papan (string): Board/listing status
- limit_price_t (float): Limit price for t+1
- limit_pct_t (float): Limit percentage for t+1
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend E2E Tests
```bash
cd frontend
npm run test:e2e
```

## Troubleshooting

### "No datasets available"
- Upload data via `/ingest/*` endpoints first
- Or use auto-scrape: `POST /ingest/scrape?source=yahoo&tickers=...`

### "Missing features" error
- Ensure ingested data has all required EOD columns
- Check validation_notes in response for details

### Supabase connection errors
- Verify SUPABASE_URL and SUPABASE_ANON_KEY in .env
- Check Row Level Security policies are set to public read

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT

## Support

- GitHub Issues: https://github.com/allamrf865/ara-models/issues
- Documentation: See `/docs` folder (coming soon)
