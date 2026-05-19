"""Ensemble ML model: LightGBM for direction, XGBoost for magnitude."""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from loguru import logger

from app.core.config import settings

MODEL_DIR = Path(settings.MODEL_STORE_PATH)
DIRECTION_MODEL_PATH = MODEL_DIR / "lgbm_direction.pkl"
MAGNITUDE_MODEL_PATH = MODEL_DIR / "xgb_magnitude.pkl"
FEATURE_NAMES_PATH = MODEL_DIR / "feature_names.pkl"


def _ensure_model_dir() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


class EnsembleModel:
    """
    Two-model ensemble:
    - LightGBM: predicts direction probability (bullish probability 0-1)
    - XGBoost: predicts expected move magnitude (%)
    Falls back to heuristic scoring if models are not trained.
    """

    def __init__(self) -> None:
        self.direction_model = None
        self.magnitude_model = None
        self.feature_names: list[str] = []
        self.is_trained = False
        self._load_models()

    def _load_models(self) -> None:
        """Load pre-trained models from disk."""
        _ensure_model_dir()
        try:
            if DIRECTION_MODEL_PATH.exists():
                with open(DIRECTION_MODEL_PATH, "rb") as f:
                    self.direction_model = pickle.load(f)

            if MAGNITUDE_MODEL_PATH.exists():
                with open(MAGNITUDE_MODEL_PATH, "rb") as f:
                    self.magnitude_model = pickle.load(f)

            if FEATURE_NAMES_PATH.exists():
                with open(FEATURE_NAMES_PATH, "rb") as f:
                    self.feature_names = pickle.load(f)

            if self.direction_model is not None:
                self.is_trained = True
                logger.info("Ensemble models loaded from {}", MODEL_DIR)
        except Exception as exc:
            logger.warning("Could not load ensemble models: {}. Using heuristics.", exc)
            self.is_trained = False

    def _save_models(self) -> None:
        """Persist trained models to disk."""
        _ensure_model_dir()
        with open(DIRECTION_MODEL_PATH, "wb") as f:
            pickle.dump(self.direction_model, f)
        with open(MAGNITUDE_MODEL_PATH, "wb") as f:
            pickle.dump(self.magnitude_model, f)
        with open(FEATURE_NAMES_PATH, "wb") as f:
            pickle.dump(self.feature_names, f)
        logger.info("Ensemble models saved to {}", MODEL_DIR)

    def train(self, X: np.ndarray, y_direction: np.ndarray, y_magnitude: np.ndarray,
              feature_names: Optional[list[str]] = None) -> Dict[str, Any]:
        """Train both models on provided features/labels."""
        try:
            import lightgbm as lgb
            import xgboost as xgb
            from sklearn.model_selection import cross_val_score

            if feature_names:
                self.feature_names = feature_names

            logger.info("Training LightGBM direction model on {} samples", len(X))
            self.direction_model = lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                num_leaves=31,
                min_child_samples=10,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1,
            )
            self.direction_model.fit(X, y_direction)

            logger.info("Training XGBoost magnitude model on {} samples", len(X))
            self.magnitude_model = xgb.XGBRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=5,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbosity=0,
            )
            self.magnitude_model.fit(X, y_magnitude)

            self.is_trained = True
            self._save_models()

            # Evaluate
            dir_cv = cross_val_score(
                lgb.LGBMClassifier(n_estimators=100, verbose=-1),
                X, y_direction, cv=3, scoring="accuracy"
            ).mean()

            return {
                "direction_cv_accuracy": round(float(dir_cv), 3),
                "samples": len(X),
                "features": len(self.feature_names),
                "status": "trained",
            }

        except ImportError as exc:
            logger.error("ML libraries not available: {}", exc)
            return {"status": "failed", "error": str(exc)}
        except Exception as exc:
            logger.error("Training failed: {}", exc)
            return {"status": "failed", "error": str(exc)}

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Predict (upside_probability %, expected_move_pct).
        Returns heuristic estimates if models are not trained.
        """
        if self.is_trained and self.direction_model is not None:
            return self._ml_predict(features)
        return self._heuristic_predict(features)

    def _ml_predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Use trained ML models for prediction."""
        try:
            from app.services.ml.feature_engineering import FeatureEngineer
            fe = FeatureEngineer()

            if self.feature_names:
                X = fe.to_array(features, self.feature_names).reshape(1, -1)
            else:
                X = np.array(list(features.values()), dtype=np.float32).reshape(1, -1)

            # Direction probability
            if hasattr(self.direction_model, "predict_proba"):
                proba = self.direction_model.predict_proba(X)[0]
                # Assumes class 1 = bullish
                upside_prob = float(proba[1]) * 100 if len(proba) > 1 else 50.0
            else:
                upside_prob = 50.0

            # Magnitude
            if self.magnitude_model is not None:
                expected_move = float(self.magnitude_model.predict(X)[0])
            else:
                expected_move = (upside_prob - 50) / 10.0

            return upside_prob, round(expected_move, 2)

        except Exception as exc:
            logger.warning("ML predict failed: {}. Using heuristics.", exc)
            return self._heuristic_predict(features)

    def _heuristic_predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Heuristic fallback based on composite feature signals.
        Returns (upside_probability, expected_move_pct).
        """
        tech_score = features.get("technical_score", 50.0)
        sentiment = features.get("sentiment_normalized", 50.0)
        catalyst = features.get("catalyst_score", 0.0)
        macro = features.get("macro_score", 50.0)
        momentum = features.get("return_5d", 0.0)
        rel_vol = features.get("relative_volume", 1.0)
        breakout = features.get("is_breakout", 0.0)
        rsi = features.get("rsi_14", 50.0)

        # Weighted composite
        composite = (
            tech_score * 0.30
            + sentiment * 0.20
            + macro * 0.15
            + min(100, 50 + momentum * 5) * 0.15
            + min(100, rel_vol * 50) * 0.10
            + (90 if breakout else 45) * 0.10
        )

        # RSI adjustment
        if 50 <= rsi <= 65:
            composite *= 1.05
        elif rsi > 75:
            composite *= 0.90

        # Catalyst boost
        if catalyst > 5:
            composite = min(100, composite * 1.10)
        elif catalyst < -3:
            composite = max(0, composite * 0.90)

        upside_probability = max(0.0, min(100.0, composite))

        # Expected move based on momentum and volatility
        volatility = features.get("volatility_20d", 20.0) / 100
        direction_strength = (upside_probability - 50) / 50
        expected_move = direction_strength * volatility * 100 * 5

        return round(upside_probability, 2), round(expected_move, 2)
