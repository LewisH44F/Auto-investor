"""Backtesting engine for simulating trading strategies."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from app.schemas.analytics import BacktestResult


class BacktestEngine:
    """Simulates entries and exits based on technical signals."""

    async def run_backtest(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
        position_size_pct: float = 10.0,
    ) -> BacktestResult:
        """
        Backtest a simple technical-signal-based strategy.
        Entry: RSI < 40 AND price > EMA_50 (oversold bounce)
        Exit: RSI > 65 OR price falls below stop_loss (1.5 × ATR)
        """
        from app.services.data_ingestion.market_data import MarketDataService
        from app.services.analysis.technical_analysis import TechnicalAnalyzer

        market_svc = MarketDataService()
        analyzer = TechnicalAnalyzer()

        # Fetch data for the period
        loop = asyncio.get_event_loop()
        import yfinance as yf
        df = await loop.run_in_executor(
            None,
            lambda: yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,
            ),
        )

        if df is None or df.empty or len(df) < 30:
            logger.warning("Insufficient backtest data for {} ({} - {})", ticker, start_date, end_date)
            return self._empty_result(ticker, start_date, end_date, initial_capital)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Compute indicators on full history
        df = analyzer.compute_indicators(df)

        capital = initial_capital
        position_size = initial_capital * position_size_pct / 100
        shares_held = 0.0
        entry_price = 0.0
        stop_loss_price = 0.0

        trades: List[Dict[str, Any]] = []
        equity_curve: List[float] = [initial_capital]

        in_position = False

        for i in range(50, len(df)):
            row = df.iloc[i]
            close = float(row.get("Close", 0))
            rsi = row.get("RSI")
            ema_50 = row.get("EMA_50")
            atr = row.get("ATR")
            macd_hist = row.get("MACD_hist")

            if close <= 0:
                continue

            if not in_position:
                # Entry signal: RSI oversold bounce with bullish structure
                rsi_ok = rsi is not None and not np.isnan(rsi) and 30 < rsi < 45
                trend_ok = ema_50 is not None and not np.isnan(ema_50) and close > ema_50
                macd_ok = macd_hist is not None and not np.isnan(macd_hist) and macd_hist > 0

                if rsi_ok and trend_ok and macd_ok and capital >= position_size:
                    shares_held = position_size / close
                    entry_price = close
                    atr_val = float(atr) if atr and not np.isnan(atr) else close * 0.02
                    stop_loss_price = close - 1.5 * atr_val
                    capital -= position_size
                    in_position = True

                    trades.append(
                        {
                            "type": "buy",
                            "date": str(df.index[i])[:10],
                            "price": round(close, 2),
                            "shares": round(shares_held, 4),
                            "rsi": round(rsi, 1) if rsi else None,
                        }
                    )

            else:
                # Exit signal
                rsi_exit = rsi is not None and not np.isnan(rsi) and rsi > 65
                stop_triggered = close < stop_loss_price

                # Also exit after 15 days max hold
                days_held = i - next(
                    (j for j in range(i, -1, -1) if not in_position), i
                )

                if rsi_exit or stop_triggered:
                    exit_price = close
                    pnl = (exit_price - entry_price) * shares_held
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    capital += shares_held * exit_price

                    trades[-1].update(
                        {
                            "exit_date": str(df.index[i])[:10],
                            "exit_price": round(exit_price, 2),
                            "pnl_pct": round(pnl_pct, 2),
                            "exit_reason": "rsi_target" if rsi_exit else "stop_loss",
                        }
                    )

                    in_position = False
                    shares_held = 0.0

            # Track equity
            portfolio_value = capital + (shares_held * close if in_position else 0)
            equity_curve.append(portfolio_value)

        # Close any open position at last price
        if in_position and len(df) > 0:
            last_price = float(df["Close"].iloc[-1])
            capital += shares_held * last_price
            pnl_pct = (last_price / entry_price - 1) * 100
            if trades:
                trades[-1].update(
                    {
                        "exit_date": str(df.index[-1])[:10],
                        "exit_price": round(last_price, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "exit_reason": "end_of_period",
                    }
                )
            equity_curve.append(capital)

        # Compute statistics
        completed_trades = [t for t in trades if "exit_price" in t]
        wins = [t for t in completed_trades if t.get("pnl_pct", 0) > 0]
        losses = [t for t in completed_trades if t.get("pnl_pct", 0) <= 0]

        win_rate = len(wins) / len(completed_trades) if completed_trades else 0.0
        avg_win = sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0.0
        avg_loss = sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0.0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

        final_capital = capital
        total_return = (final_capital - initial_capital) / initial_capital * 100

        # Max drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.cummax()
        drawdowns = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = float(drawdowns.min())

        # Sharpe ratio (simplified)
        if len(equity_curve) > 1:
            daily_returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)
                      if daily_returns.std() > 0 else 0.0)
        else:
            sharpe = 0.0

        # Average hold days
        hold_days_list = []
        for t in completed_trades:
            if "date" in t and "exit_date" in t:
                try:
                    entry_dt = datetime.strptime(t["date"], "%Y-%m-%d")
                    exit_dt = datetime.strptime(t["exit_date"], "%Y-%m-%d")
                    hold_days_list.append((exit_dt - entry_dt).days)
                except Exception:
                    pass

        avg_hold_days = sum(hold_days_list) / len(hold_days_list) if hold_days_list else 0.0

        return BacktestResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=round(final_capital, 2),
            total_return_pct=round(total_return, 2),
            win_rate=round(win_rate * 100, 2),
            total_trades=len(completed_trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            avg_win_pct=round(avg_win, 2),
            avg_loss_pct=round(avg_loss, 2),
            max_drawdown_pct=round(max_drawdown, 2),
            sharpe_ratio=round(float(sharpe), 3),
            profit_factor=round(profit_factor, 2),
            avg_hold_days=round(avg_hold_days, 1),
            trade_log=completed_trades[-20:],  # Return last 20 trades
        )

    def _empty_result(
        self, ticker: str, start_date: str, end_date: str, initial_capital: float
    ) -> BacktestResult:
        return BacktestResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            total_return_pct=0.0,
            win_rate=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            avg_win_pct=0.0,
            avg_loss_pct=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
            profit_factor=0.0,
            avg_hold_days=0.0,
            trade_log=[],
        )
