"""
体制识别模块
根据技术指标识别市场体制，支持缓冲区间
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.enums import MarketRegime

logger = logging.getLogger("aosft")


class RegimeDetector:
    def __init__(
        self,
        atr_low_buffer: float = 0.8,
        atr_high_buffer: float = 1.2
    ):
        self.atr_low_buffer = atr_low_buffer
        self.atr_high_buffer = atr_high_buffer

    def identify(
        self,
        close: float,
        ma: float,
        atr: float,
        atr_ma: float
    ) -> MarketRegime:
        is_above_ma = close > ma
        atr_ratio = atr / atr_ma if atr_ma > 0 else 1.0
        is_high_volatility = atr_ratio > self.atr_high_buffer
        is_in_buffer = self.atr_low_buffer <= atr_ratio <= self.atr_high_buffer

        if is_high_volatility and is_above_ma:
            regime = MarketRegime.BULL_VOLATILE
        elif is_high_volatility and not is_above_ma:
            regime = MarketRegime.BEAR_VOLATILE
        elif is_in_buffer and is_above_ma:
            regime = MarketRegime.TRANSITIONING
        else:
            regime = MarketRegime.LOW_VOLATILE

        logger.info(
            f"[REGIME] 体制={regime.value} "
            f"close={close:.2f} ma={ma:.2f} atr={atr:.2f} atr_ma={atr_ma:.2f} "
            f"atr_ratio={atr_ratio:.3f} above_ma={is_above_ma} "
            f"high_vol={is_high_volatility} in_buffer={is_in_buffer}"
        )

        return regime
    
    def identify_from_dataframe(self, df, current_idx: int = -1) -> MarketRegime:
        row = df.iloc[current_idx]
        return self.identify(
            close=row['close'],
            ma=row['ma'],
            atr=row['atr'],
            atr_ma=row['atr_ma']
        )
    
    def get_regime_description(self, regime: MarketRegime) -> str:
        descriptions = {
            MarketRegime.BULL_VOLATILE: "高波动上涨 → 趋势跟随区，允许做多",
            MarketRegime.BEAR_VOLATILE: "高波动下跌 → 危险区，禁止持仓",
            MarketRegime.LOW_VOLATILE: "低波动震荡 → 休息区，禁止开仓",
            MarketRegime.TRANSITIONING: "波动过渡+价格在均线上方 → 可谨慎开仓"
        }
        return descriptions.get(regime, "未知体制")
