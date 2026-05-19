"""Model store for saving and loading trained models."""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from app.core.config import settings

MODEL_DIR = Path(settings.MODEL_STORE_PATH)
WEIGHTS_FILE = MODEL_DIR / "signal_weights.json"
METADATA_FILE = MODEL_DIR / "model_metadata.json"


class ModelStore:
    """Persistent storage for model weights and metadata."""

    def __init__(self) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

    def load_signal_weights(self) -> Dict[str, float]:
        """Load learned signal weights from disk."""
        defaults = {
            "technical": 0.25,
            "sentiment": 0.20,
            "momentum": 0.20,
            "catalyst": 0.20,
            "macro": 0.10,
            "volume_anomaly": 0.05,
        }
        if not WEIGHTS_FILE.exists():
            return defaults

        try:
            with open(WEIGHTS_FILE) as f:
                weights = json.load(f)
            # Normalize to sum to 1
            total = sum(weights.values())
            if total > 0:
                return {k: v / total for k, v in weights.items()}
            return defaults
        except Exception as exc:
            logger.warning("Failed to load signal weights: {}", exc)
            return defaults

    def save_signal_weights(self, weights: Dict[str, float]) -> None:
        """Persist signal weights to disk."""
        try:
            # Normalize
            total = sum(weights.values())
            if total > 0:
                normalized = {k: v / total for k, v in weights.items()}
            else:
                normalized = weights

            with open(WEIGHTS_FILE, "w") as f:
                json.dump(normalized, f, indent=2)
            logger.info("Signal weights saved: {}", normalized)
        except Exception as exc:
            logger.error("Failed to save signal weights: {}", exc)

    def load_metadata(self) -> Dict[str, Any]:
        """Load model metadata."""
        if not METADATA_FILE.exists():
            return {
                "version": "1.0.0",
                "trained_at": None,
                "total_predictions": 0,
                "overall_win_rate": 0.0,
            }
        try:
            with open(METADATA_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Persist model metadata."""
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(METADATA_FILE, "w") as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as exc:
            logger.error("Failed to save metadata: {}", exc)

    def update_win_rate(
        self,
        new_win_rate: float,
        alpha: float = 0.1,
    ) -> float:
        """Exponential moving average update of overall win rate."""
        meta = self.load_metadata()
        current = meta.get("overall_win_rate", 0.0)
        updated = (1 - alpha) * current + alpha * new_win_rate
        meta["overall_win_rate"] = round(updated, 4)
        meta["total_predictions"] = meta.get("total_predictions", 0) + 1
        self.save_metadata(meta)
        return updated
