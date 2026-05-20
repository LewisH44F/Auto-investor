"""Portfolio tracking and AI recommendation service."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.services.market_data import MarketDataService

market_svc = MarketDataService()


class PortfolioTracker:

    async def get_holdings(self) -> list[dict]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT * FROM holdings WHERE is_active = 1 ORDER BY created_at DESC"))
            rows = result.mappings().all()
            holdings = []
            for row in rows:
                h = dict(row)
                quote = await market_svc.get_quote(h["ticker"])
                current = quote.get("price", h.get("purchase_price", 0))
                purchase = h.get("purchase_price", current)
                shares = h.get("shares", 0)
                pnl = (current - purchase) * shares
                pnl_pct = ((current - purchase) / purchase * 100) if purchase else 0
                rec, reasoning, conviction = await self._assess_holding(h["ticker"], current, purchase, pnl_pct)
                holdings.append({
                    **h,
                    "current_price": round(current, 2),
                    "unrealized_pnl": round(pnl, 2),
                    "unrealized_pnl_pct": round(pnl_pct, 2),
                    "ai_recommendation": rec,
                    "reasoning": reasoning,
                    "conviction_score": conviction,
                    "last_assessed": datetime.utcnow().isoformat(),
                })
            return holdings

    async def add_holding(self, ticker: str, shares: float, purchase_price: float, notes: str = "") -> dict:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO holdings (ticker, shares, purchase_price, purchase_date, notes, is_active, created_at)
                    VALUES (:ticker, :shares, :purchase_price, :purchase_date, :notes, 1, :created_at)
                """),
                {
                    "ticker": ticker.upper(),
                    "shares": shares,
                    "purchase_price": purchase_price,
                    "purchase_date": datetime.utcnow().isoformat(),
                    "notes": notes,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            await session.commit()
        return {"status": "added", "ticker": ticker.upper()}

    async def close_holding(self, holding_id: int, sell_price: float) -> dict:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT * FROM holdings WHERE id = :id"), {"id": holding_id}
            )
            row = result.mappings().first()
            if not row:
                return {"error": "Holding not found"}
            pnl = (sell_price - row["purchase_price"]) * row["shares"]
            await session.execute(
                text("UPDATE holdings SET is_active = 0 WHERE id = :id"),
                {"id": holding_id}
            )
            await session.execute(
                text("""
                    INSERT INTO transactions (ticker, transaction_type, shares, price, timestamp, notes, realized_pnl)
                    VALUES (:ticker, 'sell', :shares, :price, :ts, 'Closed position', :pnl)
                """),
                {"ticker": row["ticker"], "shares": row["shares"], "price": sell_price,
                 "ts": datetime.utcnow().isoformat(), "pnl": pnl}
            )
            await session.commit()
        return {"status": "closed", "realized_pnl": pnl}

    async def get_portfolio_metrics(self) -> dict:
        holdings = await self.get_holdings()
        total_invested = sum(h["purchase_price"] * h["shares"] for h in holdings)
        total_current = sum(h["current_price"] * h["shares"] for h in holdings)
        total_pnl = total_current - total_invested

        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins
                FROM transactions WHERE transaction_type = 'sell'
            """))
            row = result.mappings().first()
            total_closed = row["total"] or 0
            wins = row["wins"] or 0
            win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

        return {
            "total_positions": len(holdings),
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "total_unrealized_pnl_pct": round((total_pnl / total_invested * 100) if total_invested else 0, 2),
            "win_rate": round(win_rate, 1),
            "total_closed_positions": total_closed,
        }

    async def _assess_holding(self, ticker: str, current: float, purchase: float, pnl_pct: float) -> tuple[str, str, float]:
        """Generate AI hold/sell/buy_more/average_down recommendation."""
        try:
            from app.services.technical import TechnicalAnalyzer
            from app.services.market_data import MarketDataService
            df = await MarketDataService().fetch_ohlcv(ticker, period="1mo")
            if df is None:
                return self._simple_assess(pnl_pct)
            tech = TechnicalAnalyzer().analyze(df)
            score = tech.get("composite_score", 50)
            rsi = tech.get("rsi", 50)
            trend = tech.get("trend", "NEUTRAL")

            if pnl_pct > 10 and score < 55:
                return "sell", f"Target reached (+{pnl_pct:.1f}%). Technicals weakening (score {score:.0f}). Lock in gains.", round(score * 0.7, 1)
            elif pnl_pct < -8 and score < 45:
                return "sell", f"Stop-loss territory (-{abs(pnl_pct):.1f}%). Trend is {trend}. Cut losses to protect capital.", round(score * 0.5, 1)
            elif pnl_pct < -5 and score > 65 and rsi < 40:
                return "average_down", f"Down {abs(pnl_pct):.1f}% but technicals remain strong (RSI {rsi:.0f}, score {score:.0f}). Consider averaging down.", round(score, 1)
            elif pnl_pct > 3 and score > 72 and trend in ("BULLISH", "STRONG BULLISH"):
                return "buy_more", f"Up {pnl_pct:.1f}% with strong momentum (score {score:.0f}, {trend}). Consider adding to position.", round(score, 1)
            else:
                return "hold", f"Position up {pnl_pct:+.1f}%. Technical score {score:.0f} ({trend}). Maintain position per original thesis.", round(score, 1)
        except Exception:
            return self._simple_assess(pnl_pct)

    def _simple_assess(self, pnl_pct: float) -> tuple[str, str, float]:
        if pnl_pct > 10:
            return "sell", "Target gain reached. Consider taking profits.", 60.0
        elif pnl_pct < -8:
            return "sell", "Stop-loss level reached. Protecting capital.", 30.0
        elif pnl_pct < -4:
            return "hold", "Moderate loss. Monitor closely for further weakness.", 45.0
        else:
            return "hold", "Position within normal range. Holding as planned.", 65.0
