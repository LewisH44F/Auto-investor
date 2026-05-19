"""Portfolio tracking and AI assessment service."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Holding, PortfolioMetrics, Transaction
from app.schemas.portfolio import HoldingRead, HoldingRecommendation, PortfolioSummary


class PortfolioTracker:
    """Track holdings and generate AI recommendations."""

    async def update_prices(self, db: AsyncSession) -> List[Holding]:
        """Update current prices and P&L for all active holdings."""
        from app.services.data_ingestion.market_data import MarketDataService

        result = await db.execute(select(Holding).where(Holding.is_active == True))
        holdings = result.scalars().all()

        if not holdings:
            return []

        market_svc = MarketDataService()
        tickers = [h.ticker for h in holdings]

        quotes = await market_svc.fetch_batch_quotes(tickers)

        for holding in holdings:
            quote = quotes.get(holding.ticker, {})
            current_price = quote.get("price")

            if current_price and current_price > 0:
                holding.current_price = current_price
                holding.current_value = holding.shares * current_price
                holding.cost_basis = holding.shares * holding.purchase_price
                holding.unrealized_pnl = holding.current_value - holding.cost_basis
                holding.unrealized_pnl_pct = (
                    (holding.current_value / holding.cost_basis - 1) * 100
                    if holding.cost_basis > 0
                    else 0.0
                )

        await db.flush()
        return holdings

    async def get_summary(self, db: AsyncSession) -> PortfolioSummary:
        """Build portfolio summary with live prices."""
        holdings = await self.update_prices(db)

        total_invested = sum(
            (h.current_value or h.shares * h.purchase_price) for h in holdings
        )
        total_cost = sum(h.shares * h.purchase_price for h in holdings)
        total_pnl = total_invested - total_cost

        # Fetch cash balance from latest metrics
        from sqlalchemy import desc
        metrics_result = await db.execute(
            select(PortfolioMetrics).order_by(desc(PortfolioMetrics.date)).limit(1)
        )
        latest_metrics = metrics_result.scalar_one_or_none()
        cash = latest_metrics.cash if latest_metrics else 100000.0

        total_value = total_invested + cash
        total_pnl_pct = (total_value / (cash + total_cost) - 1) * 100 if (cash + total_cost) > 0 else 0.0

        # Sector allocations
        sector_allocs: Dict[str, float] = {}
        if total_invested > 0:
            for h in holdings:
                sector = "Unknown"  # Would need to fetch sector data
                val = h.current_value or (h.shares * h.purchase_price)
                sector_allocs[sector] = sector_allocs.get(sector, 0) + val / total_invested * 100

        return PortfolioSummary(
            total_value=round(total_value, 2),
            cash=round(cash, 2),
            invested=round(total_invested, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
            day_pnl=0.0,
            day_pnl_pct=0.0,
            num_positions=len(holdings),
            holdings=[HoldingRead.model_validate(h) for h in holdings],
            sector_allocations=sector_allocs,
            updated_at=datetime.now(timezone.utc),
        )

    async def assess_holding(
        self, holding: Holding, db: Optional[AsyncSession] = None
    ) -> HoldingRecommendation:
        """Generate AI recommendation for a single holding."""
        from app.services.ml.prediction_engine import PredictionEngine

        engine = PredictionEngine()

        # Run prediction on the holding's ticker
        pred = await engine.predict(holding.ticker, db=db, save_to_db=False)

        if pred is None:
            # Fallback: recommend hold with basic analysis
            pnl_pct = holding.unrealized_pnl_pct or 0

            if pnl_pct > 20:
                recommendation = "sell"
                reasoning = (
                    f"Holding is up {pnl_pct:.1f}%. Consider taking profits. "
                    "AI system returned no high-confidence signal for continued upside."
                )
            elif pnl_pct < -10:
                recommendation = "sell"
                reasoning = (
                    f"Holding is down {pnl_pct:.1f}%. Stop-loss consideration. "
                    "Review thesis and consider cutting losses."
                )
            else:
                recommendation = "hold"
                reasoning = "Position within normal range. No strong signal to act."

            return HoldingRecommendation(
                ticker=holding.ticker,
                holding_id=holding.id,
                recommendation=recommendation,
                conviction_score=40.0,
                reasoning=reasoning,
                current_price=holding.current_price,
                unrealized_pnl_pct=holding.unrealized_pnl_pct,
                stop_loss=holding.stop_loss_price,
                target_price=holding.target_price,
                assessed_at=datetime.now(timezone.utc),
            )

        # Use prediction to make recommendation
        confidence = pred.confidence_score
        pnl_pct = holding.unrealized_pnl_pct or 0

        if confidence >= 75 and pred.recommendation_type != "watchlist":
            recommendation = "buy_more"
            reasoning = (
                f"Strong setup detected ({confidence:.0f}% confidence). "
                f"{pred.plain_english_explanation or ''}"
            )
        elif pnl_pct >= 20 and confidence < 60:
            recommendation = "sell"
            reasoning = (
                f"Position up {pnl_pct:.1f}% and AI confidence has dropped to {confidence:.0f}%. "
                "Consider taking profits."
            )
        elif pnl_pct <= -15:
            recommendation = "sell"
            reasoning = (
                f"Position down {pnl_pct:.1f}%. Stop-loss triggered. "
                "Exit to preserve capital."
            )
        elif pnl_pct <= -5 and confidence >= 70:
            recommendation = "average_down"
            reasoning = (
                f"Position down {pnl_pct:.1f}% but AI still sees {confidence:.0f}% confidence. "
                "Consider adding at lower price if thesis is intact."
            )
        else:
            recommendation = "hold"
            reasoning = f"Position is healthy ({pnl_pct:+.1f}%). Confidence: {confidence:.0f}%."

        # Update holding's assessment
        if db:
            holding.ai_recommendation = recommendation
            holding.conviction_score = confidence
            holding.ai_reasoning = reasoning
            holding.stop_loss_price = pred.stop_loss
            holding.target_price = pred.profit_target_1
            holding.last_assessed = datetime.now(timezone.utc)
            await db.flush()

        return HoldingRecommendation(
            ticker=holding.ticker,
            holding_id=holding.id,
            recommendation=recommendation,
            conviction_score=confidence,
            reasoning=reasoning,
            current_price=holding.current_price,
            unrealized_pnl_pct=pnl_pct,
            stop_loss=pred.stop_loss,
            target_price=pred.profit_target_1,
            assessed_at=datetime.now(timezone.utc),
        )

    async def get_ai_recommendations(
        self, db: AsyncSession
    ) -> List[HoldingRecommendation]:
        """Get AI recommendations for all active holdings."""
        result = await db.execute(
            select(Holding).where(Holding.is_active == True)
        )
        holdings = result.scalars().all()

        if not holdings:
            return []

        # Update prices first
        await self.update_prices(db)

        # Generate recommendations concurrently
        tasks = [self.assess_holding(h, db) for h in holdings]
        recommendations = await asyncio.gather(*tasks, return_exceptions=True)

        valid = []
        for rec in recommendations:
            if isinstance(rec, HoldingRecommendation):
                valid.append(rec)
            else:
                logger.warning("Assessment failed: {}", rec)

        return valid

    async def record_daily_metrics(self, db: AsyncSession) -> None:
        """Snapshot today's portfolio metrics to DB."""
        summary = await self.get_summary(db)

        # Compute realized win rate
        tx_result = await db.execute(
            select(Transaction).where(Transaction.transaction_type == "sell")
        )
        sell_txs = tx_result.scalars().all()
        wins = [t for t in sell_txs if (t.realized_pnl or 0) > 0]
        win_rate = len(wins) / len(sell_txs) if sell_txs else None

        metrics = PortfolioMetrics(
            date=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
            total_value=summary.total_value,
            cash=summary.cash,
            invested=summary.invested,
            num_positions=summary.num_positions,
            total_pnl=summary.total_pnl,
            total_pnl_pct=summary.total_pnl_pct,
            win_rate=win_rate,
        )
        db.add(metrics)
        await db.flush()
        logger.info("Portfolio metrics recorded: total_value={:.2f}", summary.total_value)
