"""
策略决策引擎
管理仓位和执行决策逻辑
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.schemas import TradeSignal, Position, AccountEquity
from ..models.enums import SignalType, PositionStatus, MarketRegime
from ..models.repository import DataRepository
from ..signals.generator import SignalGenerator
from ..regime.detector import RegimeDetector
from ..indicators.calculator import TechnicalIndicators, OnchainIndicators
from ..risk.risk_interceptor import RiskInterceptor

logger = logging.getLogger("aosft")


class PositionManager:
    def __init__(
        self,
        position_ratio: float = 0.5,
        max_loss_per_trade: float = 0.05,
        stop_atr_multiplier: float = 2.0
    ):
        self.position_ratio = position_ratio
        self.max_loss_per_trade = max_loss_per_trade
        self.stop_atr_multiplier = stop_atr_multiplier
    
    def calculate_position_size(
        self,
        total_equity: float,
        entry_price: float,
        atr: float,
        position_ratio_override: Optional[float] = None
    ) -> tuple[float, float]:
        ratio = position_ratio_override or self.position_ratio
        allocated = total_equity * ratio
        
        stop_distance = self.stop_atr_multiplier * atr
        stop_price = entry_price - stop_distance
        
        max_loss_amount = total_equity * self.max_loss_per_trade
        max_position_by_risk = max_loss_amount / stop_distance if stop_distance > 0 else 0
        
        position_by_allocation = allocated / entry_price
        
        amount = min(position_by_allocation, max_position_by_risk)
        
        logger.info(
            f"[POSITION] 仓位计算: equity={total_equity:.2f} "
            f"amount={amount:.8f} stop={stop_price:.2f} "
            f"ratio={ratio:.2f}"
        )
        
        return amount, stop_price
    
    def calculate_stop_price(self, entry_price: float, atr: float) -> float:
        return entry_price - self.stop_atr_multiplier * atr
    
    def update_stop_price(self, current_stop: float, entry_price: float, atr: float) -> float:
        new_stop = self.calculate_stop_price(entry_price, atr)
        return max(current_stop, new_stop)


class StrategyEngine:
    def __init__(self, repo: DataRepository, config):
        self.repo = repo
        self.config = config
        self.position_manager = PositionManager(
            position_ratio=config.strategy.position_ratio,
            max_loss_per_trade=config.strategy.max_loss_per_trade,
            stop_atr_multiplier=config.strategy.stop_atr_multiplier
        )
        self.signal_generator = SignalGenerator(
            fear_greed_ceiling=config.strategy.fear_greed_ceiling
        )
        self.regime_detector = RegimeDetector()
        self.tech_indicators = TechnicalIndicators()
        self.onchain_indicators = OnchainIndicators()
        self.risk_interceptor = RiskInterceptor(repo)
    
    def run_daily(self) -> Optional[TradeSignal]:
        if not self.risk_interceptor.quick_check():
            logger.info("风控前置检查未通过，跳过今日交易")
            return None
        
        position = self.repo.load_current_position()
        
        if position is not None:
            return self._check_close_conditions()
        else:
            return self._check_open_conditions()
    
    def _check_open_conditions(self) -> Optional[TradeSignal]:
        ohlcv_data = self.repo.load_ohlcv(limit=50)
        if len(ohlcv_data) < 20:
            logger.warning("历史数据不足，无法计算指标")
            return None
        
        import pandas as pd
        df = pd.DataFrame(ohlcv_data)
        df = self.tech_indicators.calculate_all(
            df,
            ma_period=self.config.strategy.ma_period,
            atr_period=self.config.strategy.atr_period,
            atr_ma_period=self.config.strategy.atr_ma_period
        )
        
        latest = df.iloc[-1]
        regime = self.regime_detector.identify(
            close=latest['close'],
            ma=latest['ma'],
            atr=latest['atr'],
            atr_ma=latest['atr_ma']
        )
        
        netflow_data = self.repo.load_netflow(days=10)
        stablecoin_data = self.repo.load_stablecoin_supply(days=10)
        
        netflow_negative = False
        stable_positive = False
        
        if netflow_data:
            import pandas as pd
            nf_df = pd.DataFrame(netflow_data)
            onchain_results = self.onchain_indicators.calculate_all(
                netflow_df=nf_df,
                stablecoin_df=pd.DataFrame(stablecoin_data) if stablecoin_data else None,
                netflow_ma_days=self.config.strategy.netflow_ma_days,
                stable_change_days=self.config.strategy.stable_change_days
            )
            if not onchain_results.get('netflow_negative', pd.Series()).empty:
                netflow_negative = onchain_results['netflow_negative'].iloc[-1]
            if not onchain_results.get('stable_positive', pd.Series()).empty:
                stable_positive = onchain_results['stable_positive'].iloc[-1]
        
        fg_data = self.repo.load_fear_greed_index(days=1)
        fg_value = fg_data[0]['value'] if fg_data else None
        
        signal = self.signal_generator.generate_open_signal(
            regime=regime,
            price=latest['close'],
            netflow_negative=netflow_negative,
            stable_positive=stable_positive,
            fear_greed_value=fg_value
        )
        
        if signal:
            interception = self.risk_interceptor.intercept(signal)
            if not interception['passed']:
                logger.info(f"开仓信号被风控拦截: {interception['reason']}")
                return None
            
            position_ratio_override = interception.get('position_ratio_override')
            equity = self.repo.get_latest_equity()
            total_equity = equity['equity'] if equity else 0
            
            if total_equity > 0:
                amount, stop_price = self.position_manager.calculate_position_size(
                    total_equity=total_equity,
                    entry_price=latest['close'],
                    atr=latest['atr'],
                    position_ratio_override=position_ratio_override
                )
                logger.info(
                    f"[STRATEGY] 开仓决策: amount={amount:.8f} "
                    f"stop={stop_price:.2f}"
                )
        
        return signal
    
    def _check_close_conditions(self) -> Optional[TradeSignal]:
        position = self.repo.load_current_position()
        if not position:
            return None
        
        ohlcv_data = self.repo.load_ohlcv(limit=50)
        if not ohlcv_data:
            return None
        
        import pandas as pd
        df = pd.DataFrame(ohlcv_data)
        df = self.tech_indicators.calculate_all(df)
        latest = df.iloc[-1]
        
        regime = self.regime_detector.identify(
            close=latest['close'],
            ma=latest['ma'],
            atr=latest['atr'],
            atr_ma=latest['atr_ma']
        )
        
        stop_triggered = latest['close'] <= position['stop_price']
        
        netflow_data = self.repo.load_netflow(days=5)
        stablecoin_data = self.repo.load_stablecoin_supply(days=5)
        
        netflow_consecutive = False
        stable_consecutive = False
        
        if netflow_data:
            nf_df = pd.DataFrame(netflow_data)
            onchain_results = self.onchain_indicators.calculate_all(netflow_df=nf_df)
            if not onchain_results.get('netflow_consecutive_positive', pd.Series()).empty:
                netflow_consecutive = bool(onchain_results['netflow_consecutive_positive'].iloc[-1])
            if not onchain_results.get('stable_consecutive_negative', pd.Series()).empty:
                stable_consecutive = bool(onchain_results['stable_consecutive_negative'].iloc[-1])
        
        signal = self.signal_generator.generate_close_signal(
            regime=regime,
            price=latest['close'],
            netflow_consecutive_positive=netflow_consecutive,
            stable_consecutive_negative=stable_consecutive,
            stop_triggered=stop_triggered
        )
        
        return signal
