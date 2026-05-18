"""
集成测试：信号计算→策略决策→风控拦截 完整流程
"""
import pytest
import sqlite3
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.models.repository import DataRepository
from src.models.schemas import OHLCV, OnchainNetflow, StablecoinSupply, FearGreedIndex, Position, AccountEquity
from src.models.enums import MarketRegime, PositionStatus
from src.indicators.calculator import TechnicalIndicators, OnchainIndicators
from src.regime.detector import RegimeDetector
from src.signals.generator import SignalGenerator
from src.risk.risk_interceptor import RiskInterceptor
from src.risk.circuit_breaker_checker import CircuitBreakerChecker
from src.risk.data_freshness_checker import DataFreshnessChecker


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    from scripts.init_db import create_tables
    create_tables(db_path)
    return db_path


@pytest.fixture
def repo(test_db):
    return DataRepository(test_db)


@pytest.fixture
def sample_ohlcv_data():
    dates = [(datetime(2024, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(50)]
    np.random.seed(42)
    base_price = 42000
    prices = [base_price]
    for _ in range(49):
        prices.append(prices[-1] * (1 + np.random.normal(0.002, 0.02)))
    
    data = []
    for i, date in enumerate(dates):
        close = prices[i]
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_ = low + (high - low) * np.random.random()
        volume = np.random.uniform(500, 2000)
        data.append(OHLCV(
            symbol="BTC/USDT", date=date,
            open=round(open_, 2), high=round(high, 2),
            low=round(low, 2), close=round(close, 2),
            volume=round(volume, 2)
        ))
    return data


class TestSignalCalculationIntegration:
    def test_full_signal_pipeline(self, repo, sample_ohlcv_data):
        for ohlcv in sample_ohlcv_data:
            repo.save_ohlcv(ohlcv)
        
        ohlcv_records = repo.load_ohlcv(limit=50)
        assert len(ohlcv_records) == 50
        
        df = pd.DataFrame(ohlcv_records)
        tech = TechnicalIndicators()
        df = tech.calculate_all(df, ma_period=20, atr_period=14, atr_ma_period=30)
        
        assert 'ma' in df.columns
        assert 'atr' in df.columns
        
        detector = RegimeDetector()
        latest = df.iloc[-1]
        regime = detector.identify(
            close=latest['close'], ma=latest['ma'],
            atr=latest['atr'], atr_ma=latest['atr_ma']
        )
        assert regime in [MarketRegime.BULL_VOLATILE, MarketRegime.BEAR_VOLATILE, MarketRegime.LOW_VOLATILE]
    
    def test_regime_detection_variations(self):
        detector = RegimeDetector()
        
        bull = detector.identify(close=50000, ma=48000, atr=1500, atr_ma=1000)
        assert bull == MarketRegime.BULL_VOLATILE
        
        bear = detector.identify(close=40000, ma=45000, atr=1500, atr_ma=1000)
        assert bear == MarketRegime.BEAR_VOLATILE
        
        low = detector.identify(close=45000, ma=44000, atr=500, atr_ma=1000)
        assert low == MarketRegime.LOW_VOLATILE


class TestRiskInterceptorIntegration:
    def test_interceptor_allows_normal_trading(self, repo, sample_ohlcv_data):
        for ohlcv in sample_ohlcv_data:
            repo.save_ohlcv(ohlcv)
        
        interceptor = RiskInterceptor(repo)
        result = interceptor.intercept()
        assert 'passed' in result
        assert 'action' in result
    
    def test_circuit_breaker_blocks_trading(self, repo):
        from src.models.schemas import CircuitBreakerEvent
        from src.models.enums import CircuitBreakerType
        
        event = CircuitBreakerEvent(
            trigger_time=datetime.now().isoformat(),
            breaker_type=CircuitBreakerType.GLOBAL_DRAWDOWN,
            trigger_value=0.22,
            threshold=0.20
        )
        repo.save_circuit_breaker_event(event)
        
        checker = CircuitBreakerChecker(repo)
        status = checker.check_circuit_breaker_status()
        assert status['is_active'] is True
        assert status['allowed_position_ratio'] == 0.0


class TestDataQualityIntegration:
    def test_quality_scorer_pipeline(self, repo, sample_ohlcv_data):
        for ohlcv in sample_ohlcv_data[-5:]:
            repo.save_ohlcv(ohlcv)
        
        from src.models.data_quality_scorer import DataQualityScorer
        from src.models.data_timestamp_manager import DataTimestampManager
        
        tm = DataTimestampManager(repo.db_path)
        scorer = DataQualityScorer(tm)
        
        today = datetime.now().strftime('%Y-%m-%d')
        score = scorer.calculate_score(0)
        assert score == 1.0
        
        score = scorer.calculate_score(1)
        assert score == 1.0
        
        score = scorer.calculate_score(2)
        assert score == 0.8
        
        score = scorer.calculate_score(3)
        assert score == 0.3
        
        score = scorer.calculate_score(5)
        assert score == 0.3
    
    def test_data_freshness_check(self, repo, sample_ohlcv_data):
        for ohlcv in sample_ohlcv_data[-3:]:
            repo.save_ohlcv(ohlcv)
        
        checker = DataFreshnessChecker(repo)
        result = checker.check_data_freshness()
        assert 'all_fresh' in result


class TestRepositoryIntegration:
    def test_ohlcv_crud(self, repo, sample_ohlcv_data):
        for ohlcv in sample_ohlcv_data:
            repo.save_ohlcv(ohlcv)
        
        all_data = repo.load_ohlcv(limit=50)
        assert len(all_data) == 50
        
        latest = repo.get_latest_ohlcv()
        assert latest is not None
        assert latest['symbol'] == 'BTC/USDT'
    
    def test_signal_save_and_load(self, repo):
        from src.models.schemas import TradeSignal
        from src.models.enums import SignalType, MarketRegime
        
        signal = TradeSignal(
            timestamp=datetime.now().isoformat(),
            signal_type=SignalType.OPEN,
            symbol="BTC/USDT",
            price=50000,
            regime=MarketRegime.BULL_VOLATILE,
            netflow_condition=True,
            stable_condition=True,
            fg_condition=True,
            reason="测试信号"
        )
        
        repo.save_signal(signal)
        signals = repo.load_signals(limit=10)
        assert len(signals) >= 1
        assert signals[0]['signal_type'] == 'OPEN'
    
    def test_position_crud(self, repo):
        position = Position(
            symbol="BTC/USDT",
            entry_price=50000,
            amount=0.1,
            stop_price=48000,
            status=PositionStatus.OPEN,
            entry_time=datetime.now().isoformat()
        )
        
        repo.save_position(position)
        current = repo.load_current_position()
        assert current is not None
        assert current['status'] == 'OPEN'
        assert float(current['entry_price']) == 50000
    
    def test_equity_and_drawdown(self, repo):
        equity = AccountEquity(
            date=datetime.now().strftime('%Y-%m-%d'),
            equity=10000,
            cash=5000,
            position_value=5000,
            max_equity=10000,
            drawdown=0
        )
        
        repo.save_equity(equity)
        latest = repo.get_latest_equity()
        assert latest is not None
        assert float(latest['equity']) == 10000
    
    def test_config_crud(self, repo):
        repo.set_config('test_key', 'test_value', 'test description')
        value = repo.get_config('test_key')
        assert value == 'test_value'
