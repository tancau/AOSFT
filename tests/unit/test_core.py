"""
核心模块单元测试
"""
import pytest
import pandas as pd
import numpy as np
from src.models.enums import MarketRegime, SignalType
from src.indicators.calculator import TechnicalIndicators, OnchainIndicators
from src.regime.detector import RegimeDetector
from src.signals.generator import SignalGenerator
from src.strategy.engine import PositionManager
from src.risk.risk_interceptor import RiskInterceptor
from src.execution.gateway import OrderStateMachine, OrderTimeoutManager
from src.models.enums import OrderStatus


class TestTechnicalIndicators:
    def setup_method(self):
        self.indicator = TechnicalIndicators()
        self.df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=50).strftime('%Y-%m-%d'),
            'open': np.random.uniform(40000, 50000, 50),
            'high': np.random.uniform(50000, 52000, 50),
            'low': np.random.uniform(38000, 40000, 50),
            'close': np.random.uniform(40000, 50000, 50),
            'volume': np.random.uniform(100, 1000, 50)
        })
    
    def test_calculate_ma(self):
        ma = self.indicator.calculate_ma(self.df['close'], 20)
        assert len(ma) == 50
        assert not ma.iloc[-1] != ma.iloc[-1]  # not NaN
    
    def test_calculate_atr(self):
        atr = self.indicator.calculate_atr(
            self.df['high'], self.df['low'], self.df['close'], 14
        )
        assert len(atr) == 50
        assert atr.iloc[-1] > 0
    
    def test_calculate_all(self):
        result = self.indicator.calculate_all(self.df)
        assert 'ma' in result.columns
        assert 'atr' in result.columns
        assert 'atr_ma' in result.columns


class TestRegimeDetector:
    def setup_method(self):
        self.detector = RegimeDetector()
    
    def test_bull_volatile(self):
        regime = self.detector.identify(
            close=50000, ma=48000, atr=1500, atr_ma=1000
        )
        assert regime == MarketRegime.BULL_VOLATILE
    
    def test_bear_volatile(self):
        regime = self.detector.identify(
            close=40000, ma=45000, atr=1500, atr_ma=1000
        )
        assert regime == MarketRegime.BEAR_VOLATILE
    
    def test_low_volatile(self):
        regime = self.detector.identify(
            close=45000, ma=44000, atr=500, atr_ma=1000
        )
        assert regime == MarketRegime.LOW_VOLATILE


class TestSignalGenerator:
    def setup_method(self):
        self.generator = SignalGenerator(fear_greed_ceiling=80)
    
    def test_open_signal_all_conditions_met(self):
        signal = self.generator.generate_open_signal(
            regime=MarketRegime.BULL_VOLATILE,
            price=50000,
            netflow_negative=True,
            stable_positive=True,
            fear_greed_value=50
        )
        assert signal is not None
        assert signal.signal_type == SignalType.OPEN
    
    def test_open_signal_wrong_regime(self):
        signal = self.generator.generate_open_signal(
            regime=MarketRegime.BEAR_VOLATILE,
            price=50000,
            netflow_negative=True,
            stable_positive=True
        )
        assert signal is None
    
    def test_open_signal_netflow_not_negative(self):
        signal = self.generator.generate_open_signal(
            regime=MarketRegime.BULL_VOLATILE,
            price=50000,
            netflow_negative=False,
            stable_positive=True
        )
        assert signal is None
    
    def test_open_signal_fear_greed_too_high(self):
        signal = self.generator.generate_open_signal(
            regime=MarketRegime.BULL_VOLATILE,
            price=50000,
            netflow_negative=True,
            stable_positive=True,
            fear_greed_value=85
        )
        assert signal is None
    
    def test_close_signal_bear_regime(self):
        signal = self.generator.generate_close_signal(
            regime=MarketRegime.BEAR_VOLATILE,
            price=40000,
            netflow_consecutive_positive=False,
            stable_consecutive_negative=False
        )
        assert signal is not None
        assert signal.signal_type == SignalType.CLOSE
    
    def test_close_signal_no_condition(self):
        signal = self.generator.generate_close_signal(
            regime=MarketRegime.BULL_VOLATILE,
            price=50000,
            netflow_consecutive_positive=False,
            stable_consecutive_negative=False
        )
        assert signal is None
    
    def test_forced_close_signal(self):
        signal = self.generator.generate_forced_close_signal(
            price=40000, reason="硬止损触发"
        )
        assert signal.signal_type == SignalType.FORCED_CLOSE


class TestPositionManager:
    def setup_method(self):
        self.manager = PositionManager(
            position_ratio=0.5,
            max_loss_per_trade=0.05,
            stop_atr_multiplier=2.0
        )
    
    def test_calculate_position_size(self):
        amount, stop_price = self.manager.calculate_position_size(
            total_equity=10000,
            entry_price=50000,
            atr=1000
        )
        assert amount > 0
        assert stop_price < 50000
        assert stop_price == 50000 - 2 * 1000
    
    def test_stop_price_never_above_entry(self):
        _, stop_price = self.manager.calculate_position_size(
            total_equity=10000,
            entry_price=50000,
            atr=1000
        )
        assert stop_price < 50000
    
    def test_risk_limits_position(self):
        amount, _ = self.manager.calculate_position_size(
            total_equity=10000,
            entry_price=50000,
            atr=5000
        )
        max_loss = amount * 2 * 5000
        assert max_loss <= 10000 * 0.05 + 1


class TestOrderStateMachine:
    def setup_method(self):
        self.sm = OrderStateMachine()
    
    def test_valid_transition(self):
        assert self.sm.can_transition(OrderStatus.PENDING, OrderStatus.FILLED)
    
    def test_invalid_transition(self):
        assert not self.sm.can_transition(OrderStatus.FILLED, OrderStatus.PENDING)
    
    def test_transition(self):
        result = self.sm.transition(OrderStatus.PENDING, OrderStatus.FILLED)
        assert result == OrderStatus.FILLED
    
    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError):
            self.sm.transition(OrderStatus.FILLED, OrderStatus.CANCELLED)


class TestOnchainIndicators:
    def setup_method(self):
        self.indicator = OnchainIndicators()
    
    def test_netflow_ma(self):
        series = pd.Series([-100, -200, -150, -300, -250, -180, -220])
        result = self.indicator.calculate_netflow_ma(series, 7)
        assert len(result) == 7
    
    def test_consecutive_positive(self):
        series = pd.Series([1, 1, 1, -1, 1, 1, 1])
        result = self.indicator.check_consecutive_positive(series, 3)
        assert result.iloc[2] is True or result.iloc[2] == True
        assert result.iloc[6] is True or result.iloc[6] == True
