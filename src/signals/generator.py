"""
信号生成模块
根据体制和链上数据生成开/平仓信号
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.schemas import TradeSignal
from ..models.enums import MarketRegime, SignalType

logger = logging.getLogger("aosft")


class SignalGenerator:
    def __init__(self, fear_greed_ceiling: int = 80):
        self.fear_greed_ceiling = fear_greed_ceiling
    
    def generate_open_signal(
        self,
        regime: MarketRegime,
        price: float,
        netflow_negative: bool,
        stable_positive: bool,
        fear_greed_value: Optional[int] = None,
        symbol: str = "BTC/USDT"
    ) -> Optional[TradeSignal]:
        if regime == MarketRegime.BULL_VOLATILE:
            pass
        elif regime == MarketRegime.TRANSITIONING:
            pass
        else:
            logger.debug(f"开仓条件不满足: 体制={regime.value}(需要BULL_VOLATILE或TRANSITIONING)")
            return None
        
        if not netflow_negative:
            logger.debug("开仓条件不满足: 净流入不为负(BTC未呈囤积状态)")
            return None
        
        if not stable_positive:
            logger.debug("开仓条件不满足: 稳定币供应量未增长(无新资金入场)")
            return None
        
        if fear_greed_value is not None and fear_greed_value >= self.fear_greed_ceiling:
            logger.debug(f"开仓条件不满足: 情绪指数{fear_greed_value}≥{self.fear_greed_ceiling}(极度贪婪)")
            return None
        
        regime_desc = "BULL_VOLATILE" if regime == MarketRegime.BULL_VOLATILE else "TRANSITIONING(波动过渡)"
        signal = TradeSignal(
            timestamp=datetime.now().isoformat(),
            signal_type=SignalType.OPEN,
            symbol=symbol,
            price=price,
            regime=regime,
            netflow_condition=True,
            stable_condition=True,
            fg_condition=True,
            reason=f"开仓条件满足: {regime_desc}+净流入为负+稳定币增长"
        )
        
        logger.info(f"[SIGNAL] 开仓信号: price={price:.2f} regime={regime.value}")
        return signal
    
    def generate_close_signal(
        self,
        regime: MarketRegime,
        price: float,
        netflow_consecutive_positive: bool,
        stable_consecutive_negative: bool,
        stop_triggered: bool = False,
        symbol: str = "BTC/USDT"
    ) -> Optional[TradeSignal]:
        close_reason = None
        
        if stop_triggered:
            close_reason = "硬止损触发"
            signal_type = SignalType.STOP_LOSS
        elif regime == MarketRegime.BEAR_VOLATILE:
            close_reason = "体制转为BEAR_VOLATILE(趋势可能破坏)"
            signal_type = SignalType.CLOSE
        elif netflow_consecutive_positive:
            close_reason = "BTC净流入连续3日>0(抛压信号)"
            signal_type = SignalType.CLOSE
        elif stable_consecutive_negative:
            close_reason = "稳定币供应量连续3日下降(资金持续离场)"
            signal_type = SignalType.CLOSE
        
        if close_reason is None:
            return None
        
        signal = TradeSignal(
            timestamp=datetime.now().isoformat(),
            signal_type=signal_type,
            symbol=symbol,
            price=price,
            regime=regime,
            netflow_condition=netflow_consecutive_positive,
            stable_condition=stable_consecutive_negative,
            fg_condition=stop_triggered,
            reason=close_reason
        )
        
        logger.info(f"[SIGNAL] 平仓信号: type={signal_type.value} reason={close_reason}")
        return signal
    
    def generate_forced_close_signal(
        self,
        price: float,
        reason: str,
        symbol: str = "BTC/USDT"
    ) -> TradeSignal:
        signal = TradeSignal(
            timestamp=datetime.now().isoformat(),
            signal_type=SignalType.FORCED_CLOSE,
            symbol=symbol,
            price=price,
            regime=MarketRegime.BEAR_VOLATILE,
            netflow_condition=False,
            stable_condition=False,
            fg_condition=False,
            reason=reason
        )
        
        logger.warning(f"[SIGNAL] 强制平仓信号: reason={reason}")
        return signal
