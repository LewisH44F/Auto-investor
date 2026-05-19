"""Portfolio risk management service."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.portfolio import Holding


class RiskManager:
    """Assess and manage portfolio risk."""

    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
        holding_period: int = 1,
    ) -> float:
        """Historical Value at Risk."""
        if returns is None or len(returns) < 10:
            return 0.0
        sorted_returns = returns.sort_values()
        index = int((1 - confidence) * len(sorted_returns))
        var = abs(sorted_returns.iloc[index]) * np.sqrt(holding_period)
        return round(float(var) * 100, 2)

    async def assess_portfolio_risk(
        self, db: AsyncSession
    ) -> Dict[str, Any]:
        """Full portfolio risk assessment."""
        from app.services.data_ingestion.market_data import MarketDataService

        result = await db.execute(select(Holding).where(Holding.is_active == True))
        holdings = result.scalars().all()

        if not holdings:
            return {
                "overall_risk": "low",
                "concentration_risk": 0.0,
                "max_position_pct": 0.0,
                "var_95": 0.0,
                "alerts": [],
            }

        market_svc = MarketDataService()
        total_value = sum(
            (h.current_value or h.shares * h.purchase_price) for h in holdings
        )

        alerts: List[str] = []
        position_sizes: Dict[str, float] = {}

        for h in holdings:
            val = h.current_value or h.shares * h.purchase_price
            pct = val / total_value * 100 if total_value > 0 else 0
            position_sizes[h.ticker] = pct

            # Concentration alert
            if pct > settings.MAX_POSITION_SIZE_PCT:
                alerts.append(
                    f"{h.ticker} is {pct:.1f}% of portfolio (max: {settings.MAX_POSITION_SIZE_PCT}%)"
                )

            # Stop-loss alert
            pnl_pct = h.unrealized_pnl_pct or 0
            if pnl_pct < -settings.DEFAULT_STOP_LOSS_PCT:
                alerts.append(
                    f"{h.ticker} is down {abs(pnl_pct):.1f}% — stop-loss threshold exceeded"
                )

        max_position_pct = max(position_sizes.values()) if position_sizes else 0.0
        concentration_risk = max_position_pct

        # Overall risk rating
        if concentration_risk > 30 or len(alerts) >= 2:
            overall_risk = "high"
        elif concentration_risk > 15 or alerts:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return {
            "overall_risk": overall_risk,
            "concentration_risk": round(concentration_risk, 2),
            "max_position_pct": round(max_position_pct, 2),
            "position_sizes": position_sizes,
            "var_95": 0.0,  # Would compute from historical returns
            "num_positions": len(holdings),
            "alerts": alerts,
        }

    def recommend_position_size(
        self,
        confidence_score: float,
        risk_rating: str,
        portfolio_value: float,
        max_pct: float = 20.0,
    ) -> Dict[str, float]:
        """Kelly criterion-inspired position sizing."""
        # Base size on confidence
        if confidence_score >= 85:
            base_pct = max_pct
        elif confidence_score >= 75:
            base_pct = max_pct * 0.75
        elif confidence_score >= 65:
            base_pct = max_pct * 0.50
        else:
            base_pct = max_pct * 0.25

        # Risk adjustment
        risk_multiplier = {
            "low": 1.0,
            "medium": 0.8,
            "high": 0.6,
            "very_high": 0.4,
        }.get(risk_rating, 0.6)

        recommended_pct = round(base_pct * risk_multiplier, 1)
        recommended_dollars = round(portfolio_value * recommended_pct / 100, 2)

        return {
            "recommended_pct": recommended_pct,
            "recommended_dollars": recommended_dollars,
            "max_pct": max_pct,
        }

    def check_stop_loss(
        self,
        current_price: float,
        purchase_price: float,
        stop_loss_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Check if stop-loss should be triggered."""
        if stop_loss_pct is None:
            stop_loss_pct = settings.DEFAULT_STOP_LOSS_PCT

        stop_price = purchase_price * (1 - stop_loss_pct / 100)
        triggered = current_price <= stop_price
        current_loss_pct = (current_price / purchase_price - 1) * 100

        return {
            "triggered": triggered,
            "stop_price": round(stop_price, 2),
            "current_loss_pct": round(current_loss_pct, 2),
            "stop_loss_pct": stop_loss_pct,
        }
