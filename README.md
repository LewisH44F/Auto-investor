# AutoInvestor Intelligence System

> AI-powered stock analysis platform that runs nightly scans, surfaces high-confidence trade setups, and learns from its own track record.

---

## 1. Overview

AutoInvestor Intelligence System is a self-hosted, full-stack application that combines machine-learning predictions, real-time technical analysis, and multi-channel alerting into a single dashboard. Every evening it scans thousands of tickers, filters them through a configurable confidence gate, and delivers a ranked shortlist of swing-trade candidates directly to you — via the web UI, email, Discord, or Telegram.

The system also tracks every prediction it has ever made, back-tests those results nightly, and feeds that feedback into a gradient-boosted model that continuously improves its own accuracy.

---

## 2. Features

- **Nightly AI scan** — gradient-boosted ML model evaluates 3 000+ tickers each night using 20+ engineered features
- **Technical analysis** — RSI, MACD, Bollinger Bands, ATR, volume surge detection, support/resistance levels
- **Sentiment analysis** — financial news ingested from NewsAPI and Finnhub, scored with FinBERT
- **Confidence-gated recommendations** — only surfaces setups above a configurable threshold (default 65 %)
- **Anti-overtrading gate** — hard limits on concurrent positions and daily prediction count
- **Portfolio tracking** — live P&L, win rate, average return, Sharpe ratio
- **Self-learning engine** — nightly back-test closes the feedback loop and retrains the model weekly
- **Multi-channel alerts** — email (SMTP), Discord webhook, Telegram bot
- **Configurable trading profile** — swing / day / position, risk tolerance, max hold days
- **Full REST API** — every feature is accessible programmatically

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Browser                           │
│                    React + Vite (port 3000)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP / WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx Reverse Proxy                         │
│                       (ports 80 / 443)                          │
└──────────────┬────────────────────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌──────────────────────────┐   ┌────────────────────────────────┐
│   FastAPI Backend        │   │   Background Worker            │
│   (Uvicorn, port 8000)   │   │   (APScheduler / Celery)       │
│                          │   │                                │
│  ┌────────────────────┐  │   │  ┌──────────────────────────┐  │
│  │  REST API Routes   │  │   │  │  Nightly Analysis        │  │
│  │  Auth / JWT        │  │   │  │  ML Model Training       │  │
│  │  Portfolio Manager │  │   │  │  Back-test Engine        │  │
│  │  Alert Dispatcher  │  │   │  │  Notification Dispatch   │  │
│  └────────────────────┘  │   │  └──────────────────────────┘  │
└──────┬─────────┬──────────┘   └───────────┬────────────────────┘
       │         │                           │
       ▼         ▼                           ▼
┌───────────┐ ┌──────────┐    ┌─────────────────────────────────┐
│ PostgreSQL│ │  Redis   │    │        External APIs            │
│  (data,   │ │ (cache,  │    │  Alpha Vantage · Polygon.io     │
│  history) │ │  queue)  │    │  Finnhub · NewsAPI              │
└───────────┘ └──────────┘    └─────────────────────────────────┘
                                              │
                               ┌──────────────▼──────────────────┐
                               │        ML Model Store           │
                               │   ./ml_models/*.pkl / .joblib   │
                               └─────────────────────────────────┘
```

---

## 4. Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v2)
- At least one free API key: [Alpha Vantage](https://www.alphavantage.co/support/#api-key) or [Finnhub](https://finnhub.io/)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-org/autoinvestor.git
cd autoinvestor

# 2. Copy the example environment file and fill in your values
cp .env.example .env
nano .env   # or your preferred editor

# 3. Build and start all services
docker-compose up -d --build

# 4. Initialise the database
make migrate

# 5. (Optional) Load the seed schema
make seed

# 6. Open the dashboard
open http://localhost:3000
```

The first nightly scan runs automatically at 23:00 local time (container time). To trigger one manually:

```bash
make scan
```

---

## 5. Configuration

All configuration is done through environment variables. Copy `.env.example` to `.env` and adjust the values below.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `POSTGRES_PASSWORD` | `changeme` | Postgres superuser password |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `SECRET_KEY` | — | JWT signing secret (min 32 chars — generate with `secrets.token_hex(32)`) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | Session lifetime (30 days) |
| `ALPHA_VANTAGE_API_KEY` | — | [Alpha Vantage](https://www.alphavantage.co/) API key |
| `POLYGON_API_KEY` | — | [Polygon.io](https://polygon.io/) API key |
| `NEWS_API_KEY` | — | [NewsAPI](https://newsapi.org/) API key |
| `FINNHUB_API_KEY` | — | [Finnhub](https://finnhub.io/) API key |
| `SMTP_HOST` | `smtp.gmail.com` | Outbound email server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | — | Email sender address |
| `SMTP_PASSWORD` | — | Email sender password / app password |
| `ALERT_EMAIL_TO` | — | Alert recipient address |
| `DISCORD_WEBHOOK_URL` | — | Discord channel webhook URL |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |
| `TELEGRAM_CHAT_ID` | — | Telegram chat / channel ID |
| `MIN_CONFIDENCE_THRESHOLD` | `65` | Minimum ML confidence score (0–100) to surface a recommendation |
| `MIN_VOLUME_THRESHOLD` | `500000` | Minimum average daily volume to consider a ticker |
| `MIN_PRICE_THRESHOLD` | `5.0` | Minimum price in USD |
| `MAX_PREDICTIONS_PER_NIGHT` | `10` | Hard cap on nightly recommendations |
| `USER_TRADING_STYLE` | `swing` | `swing`, `day`, or `position` |
| `MAX_HOLD_DAYS` | `10` | Days before a position triggers a review |
| `RISK_TOLERANCE` | `medium` | `low`, `medium`, or `high` |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## 6. Usage Guide

### Dashboard

The home page shows today's top recommendations ranked by confidence score. Each card displays:

- Ticker symbol and company name
- Recommended action (BUY / HOLD / SELL)
- Confidence score with colour coding
- Entry price, target price, and stop-loss levels
- Reasoning summary from the ML model

### Portfolio Tracker

Navigate to **Portfolio** to see all open and closed positions. The tracker automatically marks predictions as closed when their hold period expires or when you manually close them.

### Alerts

Configure alert channels in **Settings → Notifications**. Alerts fire when:
- A new high-confidence recommendation is surfaced
- A held position hits its target or stop-loss
- The model's weekly accuracy drops below a threshold

### Manual Scan

Click **Run Scan Now** in the dashboard header or run `make scan` from the terminal. Useful for testing new API keys or after updating configuration.

---

## 7. API Reference

The backend exposes a fully documented REST API at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

Key endpoint groups:

| Prefix | Description |
|---|---|
| `POST /auth/login` | Obtain a JWT access token |
| `GET /predictions/` | List all predictions with optional filters |
| `GET /predictions/today` | Today's nightly scan results |
| `GET /portfolio/holdings` | Open positions |
| `GET /portfolio/performance` | Aggregate performance metrics |
| `GET /analysis/{ticker}` | Full technical + ML analysis for one ticker |
| `POST /analysis/scan` | Trigger an ad-hoc scan |
| `GET /backtests/` | Historical back-test results |
| `GET /health` | Service health check |

---

## 8. Backtesting

Every night, after generating new predictions, the worker back-tests all predictions whose hold period has expired. Results are stored in the `backtest_results` table and surfaced in the **Backtests** section of the dashboard, including:

- Win rate by confidence band
- Average return per recommendation
- Sharpe and Sortino ratios
- Confusion matrix (BUY / HOLD / SELL accuracy)

Back-test data older than 365 days is archived but not deleted, keeping the full model history intact.

---

## 9. Self-Learning Engine

The model retrains itself every Sunday at 02:00 (container time) using the accumulated back-test corpus. The training pipeline:

1. Pulls all closed predictions from the database
2. Reconstructs the feature vector for each (OHLCV + technical indicators at prediction time)
3. Labels each with the actual outcome (profit / loss, percentage return)
4. Retrains a `GradientBoostingClassifier` with cross-validated hyperparameter search
5. Saves the new model to `./ml_models/` and updates the version pointer in Redis
6. Rolls back automatically if the new model's validation accuracy is below the previous version

---

## 10. Deployment

### Production (Docker Compose)

```bash
# On your production server
git clone https://github.com/your-org/autoinvestor.git
cd autoinvestor
cp .env.example .env
# Edit .env with production credentials

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The production override adds:
- Nginx reverse proxy on ports 80 and 443
- 2 backend replicas with resource limits
- No exposed ports for postgres or redis
- `--workers 4` on Uvicorn (no `--reload`)

### SSL / TLS

Place your certificate and private key in `./nginx/ssl/` and update `./nginx/nginx.conf` to reference them. The production compose file mounts that directory read-only.

### GitHub Actions CI/CD

Pushes to `main` trigger the deploy workflow (`.github/workflows/deploy.yml`), which:
1. Builds and pushes images to GitHub Container Registry
2. SSHs into the production server and runs `docker-compose pull && up`

Set the following repository secrets in GitHub:

| Secret | Description |
|---|---|
| `DEPLOY_HOST` | Production server IP or hostname |
| `DEPLOY_USER` | SSH username |
| `DEPLOY_SSH_KEY` | Private SSH key (the public key must be in `authorized_keys` on the server) |
| `DEPLOY_PATH` | Absolute path to the project on the server |

---

## 11. Disclaimer

**AutoInvestor Intelligence System is for informational and educational purposes only.**

This software does not constitute financial advice, investment advice, trading advice, or any other type of advice. Nothing in this application should be construed as a recommendation to buy, sell, or hold any security. All trading and investment decisions are solely the responsibility of the user. Past performance of any algorithm, model, or strategy is not indicative of future results. Stock trading involves significant risk, including the possible loss of principal. Always conduct your own research and consult a qualified financial advisor before making any investment decisions.

The authors and contributors of this project accept no liability for any financial losses incurred through the use of this software.

---

## 12. License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 AutoInvestor Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
