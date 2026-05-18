"""
Paper Trading 模拟交易引擎
使用真实市场数据，但不执行真实交易，仅记录模拟交易
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.repository import DataRepository
from ..models.schemas import TradeSignal, Position, AccountEquity
from ..models.enums import PositionStatus, SignalType, MarketRegime
from ..strategy.engine import StrategyEngine
from ..risk.risk_interceptor import RiskInterceptor
from ..risk.controller import RiskController
from ..monitor.monitor import Monitor
from ..indicators.calculator import TechnicalIndicators
import pandas as pd

logger = logging.getLogger("aosft")


class PaperTradingEngine:
    def __init__(self, repo: DataRepository, config, notifier=None):
        self.repo = repo
        self.config = config
        self.strategy = StrategyEngine(repo, config)
        self.interceptor = RiskInterceptor(repo, config.data_quality.freshness_threshold)
        self.monitor = Monitor(repo, notifier)
        
        self.initial_capital = 10000.0
        self.cash = self.initial_capital
        self.position = None
        self.trades = []
        self._load_state()
    
    def _load_state(self):
        equity = self.repo.get_latest_equity()
        if equity:
            self.cash = float(equity.get('cash', self.initial_capital))
        
        pos = self.repo.load_current_position()
        if pos:
            self.position = pos
    
    def run_cycle(self) -> dict:
        result = {
            'timestamp': datetime.now().isoformat(),
            'action': 'NONE',
            'signal': None,
            'equity': 0,
            'cash': self.cash,
            'position': None,
            'pnl': 0,
            'messages': []
        }
        
        # 1. 获取最新价格
        latest = self.repo.get_latest_ohlcv()
        if not latest:
            result['messages'].append('无行情数据')
            return result
        
        current_price = float(latest['close'])
        result['current_price'] = current_price
        
        # 2. 计算当前净值
        position_value = 0
        if self.position:
            position_value = float(self.position['amount']) * current_price
        equity = self.cash + position_value
        result['equity'] = equity
        result['position_value'] = position_value
        
        # 3. 风控前置检查
        if not self.interceptor.quick_check():
            result['action'] = 'BLOCKED'
            result['messages'].append('风控拦截: 暂不交易')
            self._save_equity(equity, position_value)
            return result
        
        # 4. 生成交易信号
        signal = self.strategy.run_daily()
        result['signal'] = signal
        
        if signal is None:
            result['action'] = 'HOLD'
            result['messages'].append('无交易信号，继续持有')
            self._save_equity(equity, position_value)
            return result
        
        # 5. 执行模拟交易
        if signal.signal_type == SignalType.OPEN and self.position is None:
            self._paper_open(signal, equity)
            result['action'] = 'OPEN'
            result['messages'].append(
                f'模拟开仓: {signal.symbol} @ ${signal.price:,.2f}'
            )
        
        elif signal.signal_type.is_close_signal and self.position is not None:
            pnl = self._paper_close(signal, current_price)
            result['action'] = 'CLOSE'
            result['pnl'] = pnl
            result['messages'].append(
                f'模拟平仓: {signal.symbol} @ ${signal.price:,.2f}, '
                f'PnL=${pnl:,.2f}'
            )
        
        # 6. 更新止损价
        if self.position and signal.signal_type == SignalType.OPEN:
            ohlcv_data = self.repo.load_ohlcv(limit=50)
            if ohlcv_data:
                df = pd.DataFrame(ohlcv_data)
                tech = TechnicalIndicators()
                df = tech.calculate_all(df)
                atr = df.iloc[-1]['atr']
                new_stop = self.strategy.position_manager.update_stop_price(
                    float(self.position['stop_price']),
                    float(self.position['entry_price']),
                    atr
                )
                if new_stop > float(self.position['stop_price']):
                    self.repo.update_position(
                        self.position['id'], stop_price=new_stop
                    )
                    self.position['stop_price'] = new_stop
                    result['messages'].append(
                        f'止损上移: ${new_stop:,.2f}'
                    )
        
        # 7. 检查止损
        if self.position and current_price <= float(self.position['stop_price']):
            pnl = self._paper_close(
                TradeSignal(
                    timestamp=datetime.now().isoformat(),
                    signal_type=SignalType.STOP_LOSS,
                    symbol='BTC/USDT', price=current_price,
                    regime=MarketRegime.BEAR_VOLATILE,
                    netflow_condition=False, stable_condition=False,
                    fg_condition=False, reason='硬止损触发'
                ),
                current_price
            )
            result['action'] = 'STOP_LOSS'
            result['pnl'] = pnl
            result['messages'].append(
                f'⚠️ 硬止损触发! @ ${current_price:,.2f}, PnL=${pnl:,.2f}'
            )
        
        # 8. 保存净值
        position_value = float(self.position['amount']) * current_price if self.position else 0
        equity = self.cash + position_value
        result['equity'] = equity
        self._save_equity(equity, position_value)
        
        result['position'] = self.position
        return result
    
    def _paper_open(self, signal: TradeSignal, equity: float):
        ohlcv_data = self.repo.load_ohlcv(limit=50)
        if not ohlcv_data:
            return
        
        df = pd.DataFrame(ohlcv_data)
        tech = TechnicalIndicators()
        df = tech.calculate_all(
            df,
            ma_period=self.config.strategy.ma_period,
            atr_period=self.config.strategy.atr_period,
            atr_ma_period=self.config.strategy.atr_ma_period
        )
        atr = df.iloc[-1]['atr']
        
        amount, stop_price = self.strategy.position_manager.calculate_position_size(
            total_equity=equity,
            entry_price=signal.price,
            atr=atr
        )
        
        cost = amount * signal.price * (1 + 0.001 + 0.001)
        if cost > self.cash:
            amount = self.cash / (signal.price * (1 + 0.002))
            cost = self.cash
        
        self.cash -= cost
        
        position = Position(
            symbol=signal.symbol,
            entry_price=signal.price * (1 + 0.001),
            amount=amount,
            stop_price=stop_price,
            status=PositionStatus.OPEN,
            entry_time=datetime.now().isoformat()
        )
        self.repo.save_position(position)
        self.position = self.repo.load_current_position()
        
        self.repo.save_signal(signal)
        
        self.trades.append({
            'type': 'OPEN',
            'price': signal.price,
            'amount': amount,
            'time': datetime.now().isoformat()
        })
        
        logger.info(
            f"[PAPER-TRADE] 开仓: {amount:.8f} BTC @ ${signal.price:,.2f}, "
            f"stop=${stop_price:,.2f}, cost=${cost:,.2f}"
        )
    
    def _paper_close(self, signal: TradeSignal, current_price: float) -> float:
        if not self.position:
            return 0
        
        amount = float(self.position['amount'])
        entry_price = float(self.position['entry_price'])
        
        exit_price = current_price * (1 - 0.001)
        revenue = amount * exit_price * (1 - 0.001)
        
        pnl = revenue - amount * entry_price
        self.cash += revenue
        
        self.repo.update_position(
            self.position['id'],
            status='CLOSED',
            exit_price=exit_price,
            exit_time=datetime.now().isoformat(),
            exit_reason=signal.reason,
            pnl=pnl
        )
        
        self.repo.save_signal(signal)
        
        self.trades.append({
            'type': 'CLOSE',
            'price': exit_price,
            'amount': amount,
            'pnl': pnl,
            'time': datetime.now().isoformat()
        })
        
        self.position = None
        
        logger.info(
            f"[PAPER-TRADE] 平仓: {amount:.8f} BTC @ ${exit_price:,.2f}, "
            f"PnL=${pnl:,.2f}"
        )
        
        return pnl
    
    def _save_equity(self, equity: float, position_value: float):
        # 计算回撤
        max_equity = equity
        prev_equity = self.repo.get_latest_equity()
        if prev_equity:
            max_equity = max(float(prev_equity.get('max_equity', equity)), equity)
        
        drawdown = (max_equity - equity) / max_equity if max_equity > 0 else 0
        
        daily_pnl = 0
        if prev_equity:
            daily_pnl = equity - float(prev_equity.get('equity', equity))
        
        eq = AccountEquity(
            date=datetime.now().strftime('%Y-%m-%d'),
            equity=round(equity, 2),
            cash=round(self.cash, 2),
            position_value=round(position_value, 2),
            daily_pnl=round(daily_pnl, 2),
            max_equity=round(max_equity, 2),
            drawdown=round(drawdown, 6)
        )
        self.repo.save_equity(eq)
    
    def get_status(self) -> dict:
        latest = self.repo.get_latest_ohlcv()
        current_price = float(latest['close']) if latest else 0
        
        position_value = 0
        if self.position:
            position_value = float(self.position['amount']) * current_price
        
        equity = self.cash + position_value
        pnl = equity - self.initial_capital
        
        return {
            'mode': 'PAPER_TRADING',
            'initial_capital': self.initial_capital,
            'cash': round(self.cash, 2),
            'position_value': round(position_value, 2),
            'equity': round(equity, 2),
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl / self.initial_capital * 100, 2),
            'current_price': current_price,
            'position': self.position,
            'total_trades': len(self.trades),
        }
