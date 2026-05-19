-- ============================================================
-- AutoInvestor Intelligence System - Initial Database Schema
-- PostgreSQL 15+
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ============================================================
-- STOCKS
-- ============================================================
CREATE TABLE IF NOT EXISTS stocks (
    id                      SERIAL PRIMARY KEY,
    ticker                  VARCHAR(10) NOT NULL UNIQUE,
    name                    VARCHAR(255),
    sector                  VARCHAR(100),
    industry                VARCHAR(150),
    market_cap              DOUBLE PRECISION,
    float_shares            DOUBLE PRECISION,
    is_nasdaq               BOOLEAN DEFAULT TRUE,
    is_sp500                BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    description             TEXT,
    website                 VARCHAR(255),
    country                 VARCHAR(50),
    exchange                VARCHAR(20),
    ipo_date                TIMESTAMPTZ,
    last_updated            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stocks_ticker ON stocks(ticker);
CREATE INDEX IF NOT EXISTS ix_stocks_sector ON stocks(sector);
CREATE INDEX IF NOT EXISTS ix_stocks_is_active ON stocks(is_active);

-- ============================================================
-- STOCK PRICES
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_prices (
    id                  BIGSERIAL PRIMARY KEY,
    ticker              VARCHAR(10) NOT NULL,
    stock_id            INTEGER REFERENCES stocks(id) ON DELETE SET NULL,
    open                DOUBLE PRECISION,
    high                DOUBLE PRECISION,
    low                 DOUBLE PRECISION,
    close               DOUBLE PRECISION NOT NULL,
    adjusted_close      DOUBLE PRECISION,
    volume              BIGINT,
    pre_market_price    DOUBLE PRECISION,
    pre_market_volume   BIGINT,
    after_hours_price   DOUBLE PRECISION,
    after_hours_volume  BIGINT,
    relative_volume     DOUBLE PRECISION,
    vwap                DOUBLE PRECISION,
    dollar_volume       DOUBLE PRECISION,
    change_pct          DOUBLE PRECISION,
    gap_pct             DOUBLE PRECISION,
    interval            VARCHAR(10) DEFAULT '1d',
    timestamp           TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stock_prices_ticker_ts ON stock_prices(ticker, timestamp);
CREATE INDEX IF NOT EXISTS ix_stock_prices_timestamp ON stock_prices(timestamp);

-- ============================================================
-- STOCK FUNDAMENTALS
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_fundamentals (
    id                          SERIAL PRIMARY KEY,
    ticker                      VARCHAR(10) NOT NULL,
    stock_id                    INTEGER REFERENCES stocks(id) ON DELETE SET NULL,
    pe_ratio                    DOUBLE PRECISION,
    forward_pe                  DOUBLE PRECISION,
    pb_ratio                    DOUBLE PRECISION,
    ps_ratio                    DOUBLE PRECISION,
    peg_ratio                   DOUBLE PRECISION,
    ev_ebitda                   DOUBLE PRECISION,
    eps                         DOUBLE PRECISION,
    eps_ttm                     DOUBLE PRECISION,
    eps_growth_yoy              DOUBLE PRECISION,
    book_value_per_share        DOUBLE PRECISION,
    dividend_yield              DOUBLE PRECISION,
    revenue                     DOUBLE PRECISION,
    revenue_growth_yoy          DOUBLE PRECISION,
    revenue_growth_qoq          DOUBLE PRECISION,
    gross_margin                DOUBLE PRECISION,
    operating_margin            DOUBLE PRECISION,
    net_margin                  DOUBLE PRECISION,
    ebitda                      DOUBLE PRECISION,
    total_debt                  DOUBLE PRECISION,
    total_cash                  DOUBLE PRECISION,
    debt_to_equity              DOUBLE PRECISION,
    current_ratio               DOUBLE PRECISION,
    quick_ratio                 DOUBLE PRECISION,
    free_cash_flow              DOUBLE PRECISION,
    operating_cash_flow         DOUBLE PRECISION,
    week_52_high                DOUBLE PRECISION,
    week_52_low                 DOUBLE PRECISION,
    week_52_high_pct            DOUBLE PRECISION,
    week_52_low_pct             DOUBLE PRECISION,
    short_ratio                 DOUBLE PRECISION,
    short_float_pct             DOUBLE PRECISION,
    institutional_ownership_pct DOUBLE PRECISION,
    insider_ownership_pct       DOUBLE PRECISION,
    next_earnings_date          TIMESTAMPTZ,
    last_earnings_date          TIMESTAMPTZ,
    earnings_surprise_pct       DOUBLE PRECISION,
    report_date                 TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_fundamentals_ticker_date ON stock_fundamentals(ticker, report_date);

-- ============================================================
-- PREDICTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions (
    id                          SERIAL PRIMARY KEY,
    ticker                      VARCHAR(10) NOT NULL,
    confidence_score            DOUBLE PRECISION NOT NULL,
    upside_probability          DOUBLE PRECISION,
    downside_risk               DOUBLE PRECISION,
    volatility_score            DOUBLE PRECISION,
    momentum_score              DOUBLE PRECISION,
    sentiment_score             DOUBLE PRECISION,
    technical_score             DOUBLE PRECISION,
    catalyst_score              DOUBLE PRECISION,
    macro_score                 DOUBLE PRECISION,
    volume_anomaly_score        DOUBLE PRECISION,
    entry_zone_low              DOUBLE PRECISION,
    entry_zone_high             DOUBLE PRECISION,
    stop_loss                   DOUBLE PRECISION,
    profit_target_1             DOUBLE PRECISION,
    profit_target_2             DOUBLE PRECISION,
    expected_move_pct           DOUBLE PRECISION,
    expected_hold_duration      VARCHAR(20),
    risk_rating                 VARCHAR(20),
    recommendation_type         VARCHAR(20) NOT NULL DEFAULT 'watchlist',
    catalyst_summary            TEXT,
    technical_summary           TEXT,
    sentiment_summary           TEXT,
    plain_english_explanation   TEXT,
    signal_types                JSONB,
    feature_values              JSONB,
    actual_outcome              VARCHAR(20),
    actual_move_pct             DOUBLE PRECISION,
    outcome_recorded_at         TIMESTAMPTZ,
    prediction_error            DOUBLE PRECISION,
    is_outcome_recorded         BOOLEAN DEFAULT FALSE,
    prediction_date             TIMESTAMPTZ NOT NULL,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_predictions_ticker_date ON predictions(ticker, prediction_date);
CREATE INDEX IF NOT EXISTS ix_predictions_prediction_date ON predictions(prediction_date);
CREATE INDEX IF NOT EXISTS ix_predictions_recommendation_type ON predictions(recommendation_type);
CREATE INDEX IF NOT EXISTS ix_predictions_confidence_score ON predictions(confidence_score);

-- ============================================================
-- PREDICTION FEEDBACK
-- ============================================================
CREATE TABLE IF NOT EXISTS prediction_feedback (
    id                  SERIAL PRIMARY KEY,
    prediction_id       INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    ticker              VARCHAR(10) NOT NULL,
    actual_high         DOUBLE PRECISION,
    actual_low          DOUBLE PRECISION,
    actual_close        DOUBLE PRECISION,
    entry_price         DOUBLE PRECISION,
    holding_days        INTEGER,
    realized_gain_pct   DOUBLE PRECISION,
    max_gain_pct        DOUBLE PRECISION,
    max_loss_pct        DOUBLE PRECISION,
    hit_target_1        BOOLEAN,
    hit_target_2        BOOLEAN,
    hit_stop_loss       BOOLEAN,
    outcome_label       VARCHAR(20),
    lessons_learned     TEXT,
    weight_adjustments  JSONB,
    recorded_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_feedback_prediction_id ON prediction_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS ix_feedback_ticker ON prediction_feedback(ticker);

-- ============================================================
-- HOLDINGS
-- ============================================================
CREATE TABLE IF NOT EXISTS holdings (
    id                          SERIAL PRIMARY KEY,
    ticker                      VARCHAR(10) NOT NULL,
    shares                      DOUBLE PRECISION NOT NULL,
    purchase_price              DOUBLE PRECISION NOT NULL,
    purchase_date               TIMESTAMPTZ NOT NULL,
    notes                       TEXT,
    current_price               DOUBLE PRECISION,
    current_value               DOUBLE PRECISION,
    unrealized_pnl              DOUBLE PRECISION,
    unrealized_pnl_pct          DOUBLE PRECISION,
    cost_basis                  DOUBLE PRECISION,
    ai_recommendation           VARCHAR(30),
    conviction_score            DOUBLE PRECISION,
    ai_reasoning                TEXT,
    stop_loss_price             DOUBLE PRECISION,
    target_price                DOUBLE PRECISION,
    last_assessed               TIMESTAMPTZ,
    is_active                   BOOLEAN DEFAULT TRUE,
    is_ai_initiated             BOOLEAN DEFAULT FALSE,
    original_prediction_id      INTEGER,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_holdings_ticker ON holdings(ticker);
CREATE INDEX IF NOT EXISTS ix_holdings_is_active ON holdings(is_active);

-- ============================================================
-- TRANSACTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(10) NOT NULL,
    transaction_type    VARCHAR(10) NOT NULL,
    shares              DOUBLE PRECISION NOT NULL,
    price               DOUBLE PRECISION NOT NULL,
    total_amount        DOUBLE PRECISION,
    commission          DOUBLE PRECISION DEFAULT 0.0,
    notes               TEXT,
    timestamp           TIMESTAMPTZ DEFAULT NOW(),
    holding_id          INTEGER,
    prediction_id       INTEGER,
    realized_pnl        DOUBLE PRECISION,
    realized_pnl_pct    DOUBLE PRECISION,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_transactions_ticker ON transactions(ticker);
CREATE INDEX IF NOT EXISTS ix_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS ix_transactions_type ON transactions(transaction_type);

-- ============================================================
-- PORTFOLIO METRICS
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolio_metrics (
    id                  SERIAL PRIMARY KEY,
    date                TIMESTAMPTZ NOT NULL UNIQUE,
    total_value         DOUBLE PRECISION DEFAULT 0.0,
    cash                DOUBLE PRECISION DEFAULT 0.0,
    invested            DOUBLE PRECISION DEFAULT 0.0,
    num_positions       INTEGER DEFAULT 0,
    total_pnl           DOUBLE PRECISION DEFAULT 0.0,
    total_pnl_pct       DOUBLE PRECISION DEFAULT 0.0,
    day_pnl             DOUBLE PRECISION,
    day_pnl_pct         DOUBLE PRECISION,
    win_rate            DOUBLE PRECISION,
    sharpe_ratio        DOUBLE PRECISION,
    sortino_ratio       DOUBLE PRECISION,
    max_drawdown        DOUBLE PRECISION,
    portfolio_beta      DOUBLE PRECISION,
    var_95              DOUBLE PRECISION,
    sector_allocations  JSONB,
    top_performers      JSONB,
    worst_performers    JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_portfolio_metrics_date ON portfolio_metrics(date);

-- ============================================================
-- NEWS ARTICLES
-- ============================================================
CREATE TABLE IF NOT EXISTS news_articles (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(10),
    tickers_mentioned   VARCHAR(500),
    headline            VARCHAR(500) NOT NULL,
    summary             TEXT,
    full_text           TEXT,
    source              VARCHAR(100),
    author              VARCHAR(200),
    url                 VARCHAR(1000),
    url_hash            VARCHAR(64) UNIQUE,
    published_at        TIMESTAMPTZ,
    fetched_at          TIMESTAMPTZ DEFAULT NOW(),
    sentiment_score     DOUBLE PRECISION,
    sentiment_label     VARCHAR(20),
    impact_score        DOUBLE PRECISION,
    catalyst_type       VARCHAR(50),
    catalyst_strength   DOUBLE PRECISION,
    catalyst_duration   VARCHAR(20),
    is_processed        BOOLEAN DEFAULT FALSE,
    is_duplicate        BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_news_ticker_published ON news_articles(ticker, published_at);
CREATE INDEX IF NOT EXISTS ix_news_published_at ON news_articles(published_at);
CREATE INDEX IF NOT EXISTS ix_news_catalyst_type ON news_articles(catalyst_type);
CREATE INDEX IF NOT EXISTS ix_news_is_processed ON news_articles(is_processed);
CREATE INDEX IF NOT EXISTS ix_news_url_hash ON news_articles(url_hash);

-- ============================================================
-- SENTIMENT RECORDS
-- ============================================================
CREATE TABLE IF NOT EXISTS sentiment_records (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(10) NOT NULL,
    source              VARCHAR(50) NOT NULL,
    score               DOUBLE PRECISION NOT NULL,
    score_normalized    DOUBLE PRECISION,
    volume              INTEGER,
    bullish_count       INTEGER,
    bearish_count       INTEGER,
    neutral_count       INTEGER,
    score_prev          DOUBLE PRECISION,
    momentum            VARCHAR(20),
    raw_data            JSONB,
    timestamp           TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sentiment_ticker_ts ON sentiment_records(ticker, timestamp);
CREATE INDEX IF NOT EXISTS ix_sentiment_source ON sentiment_records(source);
CREATE INDEX IF NOT EXISTS ix_sentiment_ticker ON sentiment_records(ticker);

-- ============================================================
-- ANALYST RATINGS
-- ============================================================
CREATE TABLE IF NOT EXISTS analyst_ratings (
    id                          SERIAL PRIMARY KEY,
    ticker                      VARCHAR(10) NOT NULL,
    firm                        VARCHAR(200),
    analyst                     VARCHAR(200),
    rating                      VARCHAR(50),
    previous_rating             VARCHAR(50),
    rating_change               VARCHAR(30),
    price_target                DOUBLE PRECISION,
    previous_price_target       DOUBLE PRECISION,
    price_target_change_pct     DOUBLE PRECISION,
    notes                       TEXT,
    source_url                  VARCHAR(1000),
    timestamp                   TIMESTAMPTZ NOT NULL,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_analyst_ticker_ts ON analyst_ratings(ticker, timestamp);
CREATE INDEX IF NOT EXISTS ix_analyst_firm ON analyst_ratings(firm);

-- ============================================================
-- MODEL PERFORMANCE
-- ============================================================
CREATE TABLE IF NOT EXISTS model_performance (
    id                      SERIAL PRIMARY KEY,
    date                    TIMESTAMPTZ NOT NULL UNIQUE,
    win_rate                DOUBLE PRECISION,
    avg_confidence          DOUBLE PRECISION,
    avg_return              DOUBLE PRECISION,
    total_predictions       INTEGER,
    total_wins              INTEGER,
    total_losses            INTEGER,
    total_neutral           INTEGER,
    sharpe                  DOUBLE PRECISION,
    sortino                 DOUBLE PRECISION,
    max_drawdown            DOUBLE PRECISION,
    calmar_ratio            DOUBLE PRECISION,
    signal_type_weights     JSONB,
    signal_type_win_rates   JSONB,
    model_version           VARCHAR(50),
    notes                   TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_model_perf_date ON model_performance(date);

-- ============================================================
-- PATTERN RECORDS
-- ============================================================
CREATE TABLE IF NOT EXISTS pattern_records (
    id                      SERIAL PRIMARY KEY,
    pattern_name            VARCHAR(100) NOT NULL UNIQUE,
    description             TEXT,
    category                VARCHAR(50),
    occurrences             INTEGER DEFAULT 0,
    win_rate                DOUBLE PRECISION,
    avg_return              DOUBLE PRECISION,
    avg_hold_days           DOUBLE PRECISION,
    avg_max_gain            DOUBLE PRECISION,
    avg_max_loss            DOUBLE PRECISION,
    confidence_adjustment   DOUBLE PRECISION DEFAULT 0.0,
    last_seen               TIMESTAMPTZ,
    is_active               INTEGER DEFAULT 1,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_pattern_name ON pattern_records(pattern_name);
CREATE INDEX IF NOT EXISTS ix_pattern_win_rate ON pattern_records(win_rate);

-- ============================================================
-- LEARNING LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_logs (
    id                      SERIAL PRIMARY KEY,
    event_type              VARCHAR(50) NOT NULL,
    ticker                  VARCHAR(10),
    prediction_id           INTEGER,
    actual_vs_predicted     TEXT,
    lesson                  TEXT,
    weight_adjustment       JSONB,
    before_state            JSONB,
    after_state             JSONB,
    severity                VARCHAR(20),
    timestamp               TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_learning_log_ts ON learning_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_learning_log_event_type ON learning_logs(event_type);
CREATE INDEX IF NOT EXISTS ix_learning_log_ticker ON learning_logs(ticker);

-- ============================================================
-- SEED DATA: Initial portfolio metrics snapshot
-- ============================================================
INSERT INTO portfolio_metrics (date, total_value, cash, invested, num_positions, total_pnl, total_pnl_pct)
VALUES (DATE_TRUNC('day', NOW()), 100000.0, 100000.0, 0.0, 0, 0.0, 0.0)
ON CONFLICT (date) DO NOTHING;
