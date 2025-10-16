/*
  # Create ARA Radar Database Schema

  1. New Tables
    - `datasets`
      - `id` (uuid, primary key) - Unique dataset identifier
      - `user_id` (uuid, nullable) - Future auth support
      - `market` (text) - Market identifier (ID, US, etc)
      - `source_type` (text) - csv, excel, pdf, image, docx, audio, paste, scrape
      - `source_name` (text) - Original filename or source
      - `ingest_date` (timestamptz) - When data was ingested
      - `asof_date` (date) - Data as-of date (for EOD data)
      - `row_count` (integer) - Number of rows
      - `ticker_count` (integer) - Number of unique tickers
      - `validation_status` (text) - valid, warning, error
      - `validation_notes` (jsonb) - Validation details
      - `data` (jsonb) - Actual dataset (normalized schema)
      - `metadata` (jsonb) - Additional metadata
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)

    - `alert_schedules`
      - `id` (uuid, primary key)
      - `user_id` (uuid, nullable)
      - `market` (text)
      - `run_at_local` (time) - Time to run in local timezone
      - `timezone` (text) - Asia/Jakarta, etc
      - `k` (integer)
      - `liq` (numeric)
      - `exclude_pemantauan` (boolean)
      - `channels` (jsonb) - Array of notification channels
      - `is_active` (boolean)
      - `last_run` (timestamptz)
      - `next_run` (timestamptz)
      - `created_at` (timestamptz)

    - `trading_calendar`
      - `id` (uuid, primary key)
      - `market` (text)
      - `date` (date)
      - `is_trading_day` (boolean)
      - `notes` (text) - Holiday name, etc

  2. Security
    - Enable RLS on all tables
    - Public read access for now (auth can be added later)
    - Authenticated write access
*/

-- Create datasets table
CREATE TABLE IF NOT EXISTS datasets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  market text NOT NULL DEFAULT 'ID',
  source_type text NOT NULL,
  source_name text,
  ingest_date timestamptz NOT NULL DEFAULT now(),
  asof_date date,
  row_count integer DEFAULT 0,
  ticker_count integer DEFAULT 0,
  validation_status text DEFAULT 'pending',
  validation_notes jsonb DEFAULT '{}',
  data jsonb NOT NULL DEFAULT '[]',
  metadata jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_datasets_market ON datasets(market);
CREATE INDEX IF NOT EXISTS idx_datasets_asof_date ON datasets(asof_date);
CREATE INDEX IF NOT EXISTS idx_datasets_source_type ON datasets(source_type);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at DESC);

-- Create alert_schedules table
CREATE TABLE IF NOT EXISTS alert_schedules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  market text NOT NULL DEFAULT 'ID',
  run_at_local time NOT NULL,
  timezone text NOT NULL DEFAULT 'Asia/Jakarta',
  k integer NOT NULL DEFAULT 50,
  liq numeric NOT NULL DEFAULT 0.5,
  exclude_pemantauan boolean NOT NULL DEFAULT true,
  channels jsonb NOT NULL DEFAULT '["sse"]',
  is_active boolean NOT NULL DEFAULT true,
  last_run timestamptz,
  next_run timestamptz,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alert_schedules_next_run ON alert_schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_alert_schedules_active ON alert_schedules(is_active);

-- Create trading_calendar table
CREATE TABLE IF NOT EXISTS trading_calendar (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  market text NOT NULL,
  date date NOT NULL,
  is_trading_day boolean NOT NULL DEFAULT true,
  notes text,
  UNIQUE(market, date)
);

CREATE INDEX IF NOT EXISTS idx_trading_calendar_market_date ON trading_calendar(market, date);

-- Enable RLS
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_calendar ENABLE ROW LEVEL SECURITY;

-- Public read access policies
CREATE POLICY "Public can read datasets"
  ON datasets FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Public can read alert schedules"
  ON alert_schedules FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Public can read trading calendar"
  ON trading_calendar FOR SELECT
  TO public
  USING (true);

-- Public insert access (will be restricted to authenticated users later)
CREATE POLICY "Public can insert datasets"
  ON datasets FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Public can insert alert schedules"
  ON alert_schedules FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Public can insert trading calendar"
  ON trading_calendar FOR INSERT
  TO public
  WITH CHECK (true);

-- Insert Indonesia 2025 holidays
INSERT INTO trading_calendar (market, date, is_trading_day, notes) VALUES
  ('ID', '2025-01-01', false, 'Tahun Baru'),
  ('ID', '2025-01-29', false, 'Imlek'),
  ('ID', '2025-03-31', false, 'Idul Fitri'),
  ('ID', '2025-04-01', false, 'Idul Fitri'),
  ('ID', '2025-05-01', false, 'Hari Buruh'),
  ('ID', '2025-05-29', false, 'Kenaikan Isa Al-Masih'),
  ('ID', '2025-06-01', false, 'Pancasila'),
  ('ID', '2025-06-07', false, 'Idul Adha'),
  ('ID', '2025-06-28', false, 'Tahun Baru Islam'),
  ('ID', '2025-08-17', false, 'HUT RI'),
  ('ID', '2025-09-06', false, 'Maulid Nabi'),
  ('ID', '2025-12-25', false, 'Natal')
ON CONFLICT (market, date) DO NOTHING;
