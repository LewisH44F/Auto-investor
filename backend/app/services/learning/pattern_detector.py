"""Pattern detection service for identifying recurring profitable setups."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import PatternRecord
from app.models.prediction import Prediction


# Defined patterns to track
KNOWN_PATTERNS: Dict[str, Dict[str, Any]] = {
    "breakout_with_catalyst": {
        "description": "Breakout above resistance combined with a catalyst event",
        "category": "technical",
        "check": lambda p: (
            p.signal_types
            and p.signal_types.get("breakout")
            and p.signal_types.get("catalyst")
        ),
    },
    "high_volume_breakout": {
        "description": "Breakout with relative volume >2x average",
        "category": "technical",
        "check": lambda p: (
            p.signal_types
            and p.signal_types.get("breakout")
            and p.signal_types.get("volume_surge")
        ),
    },
    "gap_up_continuation": {
        "description": "Gap-up with continued bullish trend",
        "category": "technical",
        "check": lambda p: (
            p.signal_types
            and p.signal_types.get("gap_up")
            and p.signal_types.get("trend_bullish")
        ),
    },
    "sentiment_reversal": {
        "description": "Strong positive sentiment momentum with oversold technicals",
        "category": "sentiment",
        "check": lambda p: (
            p.signal_types
            and p.signal_types.get("sentiment_positive")
            and p.sentiment_score is not None and p.sentiment_score > 30
        ),
    },
    "catalyst_only": {
        "description": "Strong catalyst with moderate technicals",
        "category": "catalyst",
        "check": lambda p: (
            p.signal_types
            and p.signal_types.get("catalyst")
            and not p.signal_types.get("breakout")
        ),
    },
    "multi_signal_confluence": {
        "description": "Three or more bullish signals aligning",
        "category": "composite",
        "check": lambda p: (
            p.signal_types
            and sum(1 for v in p.signal_types.values() if v) >= 3
        ),
    },
    "high_confidence_primary": {
        "description": "Primary recommendation with confidence >85",
        "category": "composite",
        "check": lambda p: (
            p.recommendation_type == "primary"
            and p.confidence_score >= 85
        ),
    },
}


class PatternDetector:
    """Detect and track recurring trading patterns."""

    async def detect_and_update(self, db: AsyncSession) -> int:
        """
        Scan all recorded-outcome predictions, detect patterns,
        update PatternRecord stats in DB.
        """
        result = await db.execute(
            select(Prediction).where(Prediction.is_outcome_recorded == True)
        )
        predictions = result.scalars().all()

        if len(predictions) < 5:
            return 0

        pattern_stats: Dict[str, Dict[str, Any]] = {}

        for pred in predictions:
            is_win = pred.actual_outcome == "win"
            move = pred.actual_move_pct or 0.0

            for pattern_name, pattern_def in KNOWN_PATTERNS.items():
                try:
                    matches = pattern_def["check"](pred)
                except Exception:
                    matches = False

                if matches:
                    if pattern_name not in pattern_stats:
                        pattern_stats[pattern_name] = {
                            "wins": 0,
                            "total": 0,
                            "returns": [],
                        }
                    pattern_stats[pattern_name]["total"] += 1
                    if is_win:
                        pattern_stats[pattern_name]["wins"] += 1
                    pattern_stats[pattern_name]["returns"].append(move)

        # Upsert patterns to DB
        updated = 0
        for pattern_name, stats in pattern_stats.items():
            total = stats["total"]
            wins = stats["wins"]
            returns = stats["returns"]

            win_rate = wins / total if total > 0 else 0.0
            avg_return = sum(returns) / len(returns) if returns else 0.0

            # Compute confidence adjustment
            # If win_rate > 70%, give +5 confidence; if < 40%, penalize -5
            if win_rate >= 0.70:
                conf_adj = 5.0
            elif win_rate >= 0.55:
                conf_adj = 2.0
            elif win_rate <= 0.30:
                conf_adj = -5.0
            elif win_rate <= 0.45:
                conf_adj = -2.0
            else:
                conf_adj = 0.0

            # Check if pattern exists
            existing_result = await db.execute(
                select(PatternRecord).where(PatternRecord.pattern_name == pattern_name)
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.occurrences = total
                existing.win_rate = round(win_rate, 4)
                existing.avg_return = round(avg_return, 2)
                existing.confidence_adjustment = conf_adj
                existing.last_seen = datetime.now(timezone.utc)
            else:
                desc_def = KNOWN_PATTERNS.get(pattern_name, {})
                pattern_record = PatternRecord(
                    pattern_name=pattern_name,
                    description=desc_def.get("description", ""),
                    category=desc_def.get("category", "composite"),
                    occurrences=total,
                    win_rate=round(win_rate, 4),
                    avg_return=round(avg_return, 2),
                    confidence_adjustment=conf_adj,
                    last_seen=datetime.now(timezone.utc),
                )
                db.add(pattern_record)

            updated += 1

        await db.flush()
        logger.info("Pattern detection updated {} patterns", updated)
        return updated

    async def get_applicable_patterns(
        self, prediction: Prediction, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get patterns that apply to a prediction (for confidence adjustment)."""
        result = await db.execute(select(PatternRecord))
        all_patterns = result.scalars().all()

        applicable = []
        for pat in all_patterns:
            pattern_def = KNOWN_PATTERNS.get(pat.pattern_name)
            if pattern_def:
                try:
                    if pattern_def["check"](prediction):
                        applicable.append(
                            {
                                "name": pat.pattern_name,
                                "win_rate": pat.win_rate,
                                "confidence_adjustment": pat.confidence_adjustment,
                                "occurrences": pat.occurrences,
                            }
                        )
                except Exception:
                    pass

        return applicable

    def apply_pattern_adjustments(
        self, base_confidence: float, patterns: List[Dict[str, Any]]
    ) -> float:
        """Apply pattern-based confidence adjustments."""
        total_adj = sum(p.get("confidence_adjustment", 0) for p in patterns)
        # Cap total adjustment to ±10
        total_adj = max(-10.0, min(10.0, total_adj))
        adjusted = base_confidence + total_adj
        return max(0.0, min(100.0, adjusted))
