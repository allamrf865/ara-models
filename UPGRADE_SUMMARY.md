# ARA Radar v1 → v2 Upgrade Summary

## What Changed

### Backend Upgrades
1. **Multi-Ingest System**: Added 8 data ingestion endpoints
   - CSV, Excel, PDF, Image, DOCX, Audio, Paste, Scrape
   - Automatic validation & normalization
   - Persistent storage in Supabase

2. **Calendar System**: Trading day management
   - GET /calendar - List trading days
   - GET /next_trading_day - Calculate next trading day
   - Indonesia 2025 holidays pre-loaded

3. **Scheduled Alerts**: POST /alerts/schedule
   - Run after market close
   - Timezone-aware scheduling
   - Multi-channel support

4. **Dataset Management**:
   - GET /datasets - List all ingested data
   - Dataset provenance tracking
   - Validation status per dataset

5. **New Dependencies**:
   - Supabase client
   - pdfplumber + pytesseract (OCR)
   - python-docx
   - faster-whisper
   - yfinance

### Frontend Upgrades
1. **Ingest Wizard** (/ingest):
   - Multi-tab interface
   - Real-time validation
   - Progress tracking
   - Data provenance display

2. **Dashboard Enhancements**:
   - Market selector dropdown
   - Link to Ingest Wizard
   - Dataset info display
   - Auto-refresh from latest dataset

3. **New API Functions**:
   - fetchDatasets()
   - Market parameter support

### Database (Supabase)
New tables:
- `datasets` - Ingested data storage
- `alert_schedules` - Scheduled jobs
- `trading_calendar` - Market holidays

## Migration Steps

### 1. Backend Migration
```bash
cd backend
pip install -r requirements.txt  # New dependencies
# Set SUPABASE_URL and SUPABASE_ANON_KEY in .env
```

### 2. Database Migration
Already applied via Supabase MCP:
- Created 3 tables with RLS
- Inserted Indonesia 2025 holidays

### 3. Frontend Migration
```bash
cd frontend
npm install  # Same dependencies
# No breaking changes to existing pages
```

## Backward Compatibility

✅ **Fully Backward Compatible**
- All v1 endpoints still work
- POST /score still available (legacy)
- GET /score_latest enhanced but compatible
- Existing dashboards work without changes

## New Workflows

### Workflow 1: One-Click Auto-Fetch
```
User clicks "Auto-Fetch" in Ingest Wizard
  ↓
POST /ingest/scrape?source=yahoo&tickers=BBCA,BBRI
  ↓
Returns dataset_id
  ↓
Dashboard auto-refreshes with new data
```

### Workflow 2: Upload & Score
```
User uploads CSV in Ingest Wizard
  ↓
POST /ingest/csv
  ↓
Backend validates & normalizes
  ↓
Saves to Supabase with dataset_id
  ↓
GET /score_latest uses latest dataset
  ↓
Results displayed in dashboard
```

### Workflow 3: Scheduled Alerts
```
User sets alert for 4:30 PM Jakarta time
  ↓
POST /alerts/schedule
  ↓
Saved in alert_schedules table
  ↓
Backend cron checks next_run
  ↓
Executes scoring after market close
  ↓
Pushes alerts via SSE
```

## Key Benefits

1. **No Manual Data Prep**: Users upload any format
2. **One-Click Workflows**: Auto-fetch eliminates upload step
3. **Data Provenance**: Track where data came from
4. **Flexible Scheduling**: Alerts run automatically
5. **Multi-Market**: Support for ID, US, and more

## Testing Checklist

- [ ] Upload CSV via /ingest/csv
- [ ] Auto-fetch from Yahoo Finance
- [ ] View datasets list
- [ ] Score latest dataset
- [ ] Schedule alert for next day
- [ ] Verify trading calendar
- [ ] Check real-time SSE alerts

## Files Modified

### Backend
- app.py (replaced with app_upgraded.py)
- requirements.txt (added 7 packages)
- .env.example (added Supabase vars)

### Backend (New Files)
- ingest.py (8 ingestion functions)
- db.py (Supabase operations)
- calendar_utils.py (trading days)

### Frontend
- app/dashboard/page.tsx (added market selector)
- lib/api.ts (added market param)

### Frontend (New Files)
- app/ingest/page.tsx (Ingest Wizard)

### Database
- 3 new Supabase tables
- RLS policies
- Indonesia holidays data

## Next Steps

1. Deploy backend to Render with Supabase vars
2. Deploy frontend to Netlify
3. Test all ingest methods
4. Set up scheduled alerts
5. Monitor Supabase usage

