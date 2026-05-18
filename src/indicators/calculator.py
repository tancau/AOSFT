"""
技术指标计算模块
计算MA、ATR、净流入趋势、稳定币变化等指标
"""
import logging
import pandas as pd
import numpy as np
from typing import Optional

logger = logging.getLogger("aosft")


class TechnicalIndicators:
    @staticmethod
    def calculate_ma(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                      period: int = 14) -> pd.Series:
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=1).mean()
        return atr
    
    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()
    
    def calculate_all(self, df: pd.DataFrame, ma_period: int = 20,
                      atr_period: int = 14, atr_ma_period: int = 30) -> pd.DataFrame:
        result = df.copy()
        
        result['ma'] = self.calculate_ma(result['close'], ma_period)
        result['atr'] = self.calculate_atr(
            result['high'], result['low'], result['close'], atr_period
        )
        result['atr_ma'] = self.calculate_ma(result['atr'], atr_ma_period)
        
        logger.debug(f"计算技术指标完成: MA({ma_period}), ATR({atr_period}), ATR_MA({atr_ma_period})")
        return result


class OnchainIndicators:
    @staticmethod
    def calculate_netflow_ma(netflow: pd.Series, period: int = 7) -> pd.Series:
        return netflow.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def calculate_stablecoin_change(total_supply: pd.Series,
                                     period: int = 7) -> pd.Series:
        return total_supply.pct_change(periods=period)
    
    @staticmethod
    def check_consecutive_positive(series: pd.Series, days: int = 3) -> pd.Series:
        rolling_sum = series.rolling(window=days, min_periods=days).sum()
        return rolling_sum == days
    
    @staticmethod
    def check_consecutive_negative(series: pd.Series, days: int = 3) -> pd.Series:
        rolling_sum = series.rolling(window=days, min_periods=days).sum()
        return rolling_sum == -days
    
    def calculate_all(self, netflow_df: pd.DataFrame = None,
                      stablecoin_df: pd.DataFrame = None,
                      netflow_ma_days: int = 7,
                      stable_change_days: int = 7,
                      confirm_days: int = 3) -> dict:
        result = {}
        
        if netflow_df is not None and 'netflow' in netflow_df.columns:
            result['netflow_ma'] = self.calculate_netflow_ma(
                netflow_df['netflow'], netflow_ma_days
            )
            result['netflow_negative'] = result['netflow_ma'] < 0
            result['netflow_consecutive_positive'] = self.check_consecutive_positive(
                (netflow_df['netflow'] > 0).astype(int) * 2 - 1, confirm_days
            )
        
        if stablecoin_df is not None and 'total_supply' in stablecoin_df.columns:
            result['stable_change'] = self.calculate_stablecoin_change(
                stablecoin_df['total_supply'], stable_change_days
            )
            result['stable_positive'] = result['stable_change'] > 0
            result['stable_consecutive_negative'] = self.check_consecutive_negative(
                (result['stable_change'] > 0).astype(int) * 2 - 1, confirm_days
            )
        
        logger.debug("链上指标计算完成")
        return result
