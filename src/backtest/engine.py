"""
回测系统
在历史数据上验证策略表现
"""
import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from ..models.enums import MarketRegime, SignalType
from ..indicators.calculator import TechnicalIndicators, OnchainIndicators
from ..regime.detector import RegimeDetector
from ..signals.generator import SignalGenerator
from ..strategy.engine import PositionManager

logger = logging.getLogger("aosft")


@dataclass
class BacktestTrade:
    entry_date: str
    entry_price: float
    exit_date: str = ""
    exit_price: float = 0
    exit_reason: str = ""
    amount: float = 0
    pnl: float = 0
    pnl_pct: float = 0


@dataclass
class BacktestResult:
    trades: List[BacktestTrade] = field(default_factory=list)
    initial_capital: float = 10000.0
    final_capital: float = 10000.0
    total_return: float = 0
    annual_return: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    max_consecutive_losses: int = 0
    total_trades: int = 0


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_rate: float = 0.001,
        slippage: float = 0.001,
        position_ratio: float = 0.5,
        stop_atr_multiplier: float = 2.0,
        max_loss_per_trade: float = 0.05,
        fear_greed_ceiling: int = 80,
        ma_period: int = 20,
        atr_period: int = 14,
        atr_ma_period: int = 30,
        netflow_ma_days: int = 7,
        stable_change_days: int = 7,
        confirm_days: int = 3
    ):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.ma_period = ma_period
        self.atr_period = atr_period
        self.atr_ma_period = atr_ma_period
        self.netflow_ma_days = netflow_ma_days
        self.stable_change_days = stable_change_days
        self.confirm_days = confirm_days
        
        self.tech = TechnicalIndicators()
        self.onchain = OnchainIndicators()
        self.regime_detector = RegimeDetector()
        self.signal_gen = SignalGenerator(fear_greed_ceiling)
        self.position_mgr = PositionManager(
            position_ratio, max_loss_per_trade, stop_atr_multiplier
        )
    
    def run(
        self,
        ohlcv_df: pd.DataFrame,
        netflow_df: Optional[pd.DataFrame] = None,
        stablecoin_df: Optional[pd.DataFrame] = None,
        fg_df: Optional[pd.DataFrame] = None
    ) -> BacktestResult:
        result = BacktestResult(initial_capital=self.initial_capital)
        
        ohlcv_df = self.tech.calculate_all(
            ohlcv_df, self.ma_period, self.atr_period, self.atr_ma_period
        )
        
        onchain_results = {}
        if netflow_df is not None:
            onchain_results = self.onchain.calculate_all(
                netflow_df, stablecoin_df,
                self.netflow_ma_days, self.stable_change_days, self.confirm_days
            )
        
        capital = self.initial_capital
        position: Optional[BacktestTrade] = None
        equity_curve = []
        
        for i in range(self.atr_period, len(ohlcv_df)):
            row = ohlcv_df.iloc[i]
            date = row['date']
            price = row['close']
            
            regime = self.regime_detector.identify(
                close=price, ma=row['ma'],
                atr=row['atr'], atr_ma=row['atr_ma']
            )
            
            netflow_neg = True
            stable_pos = True
            netflow_consec_pos = False
            stable_consec_neg = False
            
            if onchain_results.get('netflow_negative') is not None:
                idx = min(i, len(onchain_results['netflow_negative']) - 1)
                netflow_neg = bool(onchain_results['netflow_negative'].iloc[idx])
            if onchain_results.get('stable_positive') is not None:
                idx = min(i, len(onchain_results['stable_positive']) - 1)
                stable_pos = bool(onchain_results['stable_positive'].iloc[idx])
            if onchain_results.get('netflow_consecutive_positive') is not None:
                idx = min(i, len(onchain_results['netflow_consecutive_positive']) - 1)
                netflow_consec_pos = bool(onchain_results['netflow_consecutive_positive'].iloc[idx])
            if onchain_results.get('stable_consecutive_negative') is not None:
                idx = min(i, len(onchain_results['stable_consecutive_negative']) - 1)
                stable_consec_neg = bool(onchain_results['stable_consecutive_negative'].iloc[idx])
            
            fg_value = None
            if fg_df is not None and date in fg_df['date'].values:
                fg_value = int(fg_df[fg_df['date'] == date]['value'].iloc[0])
            
            if position is None:
                signal = self.signal_gen.generate_open_signal(
                    regime=regime, price=price,
                    netflow_negative=netflow_neg,
                    stable_positive=stable_pos,
                    fear_greed_value=fg_value
                )
                
                if signal:
                    amount, stop_price = self.position_mgr.calculate_position_size(
                        capital, price, row['atr']
                    )
                    
                    cost = amount * price * (1 + self.fee_rate + self.slippage)
                    if cost <= capital:
                        position = BacktestTrade(
                            entry_date=date,
                            entry_price=price * (1 + self.slippage),
                            amount=amount
                        )
                        capital -= cost
            
            else:
                stop_triggered = price <= (position.entry_price - 2 * row['atr'])
                
                close_signal = self.signal_gen.generate_close_signal(
                    regime=regime, price=price,
                    netflow_consecutive_positive=netflow_consec_pos,
                    stable_consecutive_negative=stable_consec_neg,
                    stop_triggered=stop_triggered
                )
                
                if close_signal:
                    exit_price = price * (1 - self.slippage)
                    revenue = position.amount * exit_price * (1 - self.fee_rate)
                    pnl = revenue - position.amount * position.entry_price
                    
                    position.exit_date = date
                    position.exit_price = exit_price
                    position.exit_reason = close_signal.reason
                    position.pnl = pnl
                    position.pnl_pct = pnl / (position.amount * position.entry_price)
                    
                    capital += revenue
                    result.trades.append(position)
                    position = None
            
            if position:
                equity = capital + position.amount * price
            else:
                equity = capital
            equity_curve.append(equity)
        
        if position:
            last_price = ohlcv_df.iloc[-1]['close']
            revenue = position.amount * last_price * (1 - self.fee_rate - self.slippage)
            position.exit_date = ohlcv_df.iloc[-1]['date']
            position.exit_price = last_price
            position.exit_reason = "回测结束"
            position.pnl = revenue - position.amount * position.entry_price
            capital += revenue
            result.trades.append(position)
            equity_curve.append(capital)
        
        result.final_capital = capital
        self._calculate_metrics(result, equity_curve)
        
        logger.info(
            f"[BACKTEST] 完成: trades={result.total_trades} "
            f"return={result.total_return*100:.2f}% "
            f"max_dd={result.max_drawdown*100:.2f}% "
            f"sharpe={result.sharpe_ratio:.2f}"
        )
        
        return result
    
    def _calculate_metrics(self, result: BacktestResult, equity_curve: list):
        result.total_trades = len(result.trades)
        result.total_return = (result.final_capital / result.initial_capital) - 1
        
        if result.total_trades > 0:
            wins = [t for t in result.trades if t.pnl > 0]
            losses = [t for t in result.trades if t.pnl < 0]
            result.win_rate = len(wins) / result.total_trades
            
            avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
            avg_loss = abs(sum(t.pnl for t in losses) / len(losses)) if losses else 1
            result.profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            
            consecutive = 0
            max_consecutive = 0
            for t in result.trades:
                if t.pnl < 0:
                    consecutive += 1
                    max_consecutive = max(max_consecutive, consecutive)
                else:
                    consecutive = 0
            result.max_consecutive_losses = max_consecutive
        
        if len(equity_curve) > 1:
            equity_series = pd.Series(equity_curve)
            running_max = equity_series.cummax()
            drawdown = (running_max - equity_series) / running_max
            result.max_drawdown = drawdown.max()
            
            daily_returns = equity_series.pct_change().dropna()
            if len(daily_returns) > 0 and daily_returns.std() > 0:
                result.sharpe_ratio = (
                    daily_returns.mean() / daily_returns.std() * np.sqrt(365)
                )
            
            days = len(equity_curve)
            if days > 0:
                result.annual_return = (
                    (result.final_capital / result.initial_capital) ** (365 / days) - 1
                )
