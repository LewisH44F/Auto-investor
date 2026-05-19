"""Fundamental analysis service."""

from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger


class FundamentalAnalyzer:
    """Analyze fundamental financial metrics."""

    def score_fundamentals(self, info: Dict[str, Any]) -> float:
        """
        Score fundamental quality (0-100).
        Uses PE, growth, margins, debt metrics.
        """
        score = 50.0
        weight_total = 0.0
        weighted_sum = 0.0

        # Earnings growth (most important)
        eps_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
        if eps_growth is not None:
            g_score = min(100.0, max(0.0, 50 + eps_growth * 100))
            weighted_sum += g_score * 0.25
            weight_total += 0.25

        # Revenue growth
        rev_growth = info.get("revenueGrowth")
        if rev_growth is not None:
            r_score = min(100.0, max(0.0, 50 + rev_growth * 100))
            weighted_sum += r_score * 0.20
            weight_total += 0.20

        # Profit margins
        profit_margin = info.get("profitMargins")
        if profit_margin is not None:
            m_score = min(100.0, max(0.0, profit_margin * 300))
            weighted_sum += m_score * 0.15
            weight_total += 0.15

        # PE ratio (lower is generally better, penalize >50)
        pe = info.get("trailingPE") or info.get("forwardPE")
        if pe is not None and pe > 0:
            if pe < 15:
                pe_score = 85.0
            elif pe < 25:
                pe_score = 70.0
            elif pe < 40:
                pe_score = 50.0
            elif pe < 60:
                pe_score = 35.0
            else:
                pe_score = 20.0
            weighted_sum += pe_score * 0.15
            weight_total += 0.15

        # Debt to equity
        de = info.get("debtToEquity")
        if de is not None:
            if de < 0.5:
                de_score = 85.0
            elif de < 1.0:
                de_score = 70.0
            elif de < 2.0:
                de_score = 50.0
            else:
                de_score = 25.0
            weighted_sum += de_score * 0.10
            weight_total += 0.10

        # Return on equity
        roe = info.get("returnOnEquity")
        if roe is not None:
            roe_score = min(100.0, max(0.0, roe * 300))
            weighted_sum += roe_score * 0.15
            weight_total += 0.15

        if weight_total > 0:
            score = weighted_sum / weight_total

        return round(max(0.0, min(100.0, score)), 2)

    async def analyze(self, ticker: str) -> Dict[str, Any]:
        """Fetch and analyze fundamentals for a ticker."""
        from app.services.data_ingestion.market_data import MarketDataService

        market_svc = MarketDataService()
        info = await market_svc.fetch_ticker_info(ticker)

        if not info:
            return {"score": 50.0, "data": {}}

        fundamental_score = self.score_fundamentals(info)

        return {
            "score": fundamental_score,
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "profit_margin": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "return_on_equity": info.get("returnOnEquity"),
            "free_cashflow": info.get("freeCashflow"),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
