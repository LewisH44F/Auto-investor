"""Catalyst detection engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


CATALYST_RULES: Dict[str, Dict[str, Any]] = {
    "earnings_beat": {
        "keywords": ["beat", "exceeded", "surpassed", "topped", "record earnings", "earnings beat"],
        "min_keywords": 1,
        "strength": 8.0,
        "duration": "3d",
    },
    "earnings_miss": {
        "keywords": ["miss", "missed", "fell short", "below expectations", "disappointing earnings"],
        "min_keywords": 1,
        "strength": 7.0,
        "duration": "3d",
    },
    "revenue_surprise": {
        "keywords": ["revenue beat", "revenue surge", "revenue record", "revenue growth"],
        "min_keywords": 1,
        "strength": 6.0,
        "duration": "3d",
    },
    "fda_approval": {
        "keywords": ["fda approved", "fda approval", "approved by fda", "nda approval", "bla approval"],
        "min_keywords": 1,
        "strength": 9.0,
        "duration": "1w",
    },
    "fda_rejection": {
        "keywords": ["fda rejected", "fda rejection", "complete response letter", "crl"],
        "min_keywords": 1,
        "strength": 8.0,
        "duration": "1w",
    },
    "merger_acquisition": {
        "keywords": ["acquire", "acquisition", "merger", "buyout", "takeover", "m&a deal"],
        "min_keywords": 1,
        "strength": 8.5,
        "duration": "1w",
    },
    "analyst_upgrade": {
        "keywords": ["upgrade", "upgraded", "buy rating", "outperform", "strong buy", "raised target"],
        "min_keywords": 1,
        "strength": 5.0,
        "duration": "1d",
    },
    "analyst_downgrade": {
        "keywords": ["downgrade", "downgraded", "sell rating", "underperform", "underweight", "cut target"],
        "min_keywords": 1,
        "strength": 5.0,
        "duration": "1d",
    },
    "government_contract": {
        "keywords": ["government contract", "defense contract", "pentagon", "dod contract", "billion award"],
        "min_keywords": 1,
        "strength": 7.0,
        "duration": "1d",
    },
    "partnership": {
        "keywords": ["partnership", "collaboration", "agreement", "joint venture", "alliance", "strategic deal"],
        "min_keywords": 1,
        "strength": 5.5,
        "duration": "1d",
    },
    "leadership_change": {
        "keywords": ["new ceo", "new cfo", "appoints", "resign", "step down", "leadership change"],
        "min_keywords": 1,
        "strength": 4.0,
        "duration": "3d",
    },
    "share_buyback": {
        "keywords": ["buyback", "repurchase", "buy back", "share repurchase"],
        "min_keywords": 1,
        "strength": 5.0,
        "duration": "3d",
    },
    "dividend": {
        "keywords": ["dividend", "quarterly dividend", "special dividend", "dividend increase"],
        "min_keywords": 1,
        "strength": 4.5,
        "duration": "1d",
    },
    "short_squeeze": {
        "keywords": ["short squeeze", "short interest", "high short", "heavily shorted"],
        "min_keywords": 1,
        "strength": 6.0,
        "duration": "1d",
    },
    "macro_positive": {
        "keywords": ["rate cut", "fed cut", "stimulus", "low inflation", "strong jobs"],
        "min_keywords": 1,
        "strength": 4.0,
        "duration": "1w",
    },
    "macro_negative": {
        "keywords": ["rate hike", "fed hike", "recession", "high inflation", "weak jobs"],
        "min_keywords": 1,
        "strength": 4.0,
        "duration": "1w",
    },
}


class CatalystDetector:
    """Detect and score catalysts from news text."""

    def detect_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all catalysts present in text.
        Returns list of {type, strength, duration, direction}.
        """
        text_lower = text.lower()
        detected = []

        for catalyst_name, rule in CATALYST_RULES.items():
            keywords = rule["keywords"]
            min_kw = rule.get("min_keywords", 1)

            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= min_kw:
                # Determine direction
                negative_catalysts = {
                    "earnings_miss", "fda_rejection", "analyst_downgrade", "macro_negative"
                }
                direction = "negative" if catalyst_name in negative_catalysts else "positive"

                detected.append(
                    {
                        "type": catalyst_name,
                        "strength": rule["strength"],
                        "duration": rule["duration"],
                        "direction": direction,
                        "keyword_matches": matches,
                    }
                )

        return detected

    def score_catalysts(
        self, catalysts: List[Dict[str, Any]]
    ) -> Tuple[float, str, str]:
        """
        Return (net_score, primary_type, duration).
        Score is -10 to +10 (positive = bullish).
        """
        if not catalysts:
            return 0.0, "none", "1d"

        net_score = 0.0
        for cat in catalysts:
            direction_mult = 1.0 if cat["direction"] == "positive" else -1.0
            net_score += cat["strength"] * direction_mult

        net_score = max(-10.0, min(10.0, net_score))

        # Primary catalyst = highest strength
        primary = max(catalysts, key=lambda c: c["strength"])

        return round(net_score, 2), primary["type"], primary["duration"]

    async def analyze_ticker_catalysts(self, ticker: str) -> Dict[str, Any]:
        """Analyze catalysts from recent news for a ticker."""
        from app.services.data_ingestion.news_scraper import NewsScraper

        scraper = NewsScraper()
        articles = await scraper.get_ticker_news(ticker, limit=10)

        all_catalysts: List[Dict[str, Any]] = []
        catalyst_summary_parts: List[str] = []

        for article in articles:
            text = f"{article.get('headline', '')} {article.get('summary', '')}"
            detected = self.detect_from_text(text)
            all_catalysts.extend(detected)

            if detected:
                catalyst_summary_parts.append(
                    f"{article.get('headline', '')[:80]} [{detected[0]['type']}]"
                )

        net_score, primary_type, duration = self.score_catalysts(all_catalysts)

        catalyst_types = list({c["type"] for c in all_catalysts})
        summary = (
            "; ".join(catalyst_summary_parts[:3])
            if catalyst_summary_parts
            else "No significant catalysts detected"
        )

        return {
            "score": net_score,
            "primary_type": primary_type,
            "duration": duration,
            "all_types": catalyst_types,
            "count": len(all_catalysts),
            "summary": summary,
            "is_bullish": net_score > 0,
        }
