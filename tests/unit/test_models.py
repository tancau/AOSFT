"""
数据模型单元测试
"""
import pytest
from src.models.enums import MarketRegime, SignalType, PositionStatus, OrderStatus
from src.models.schemas import (
    OHLCV, OnchainNetflow, StablecoinSupply, FearGreedIndex,
    TradeSignal, Position, AccountEquity, Order, DataQuality
)


class TestMarketRegime:
    def test_bull_volatile_allows_long(self):
        assert MarketRegime.BULL_VOLATILE.allow_long is True
    
    def test_bear_volatile_dangerous(self):
        assert MarketRegime.BEAR_VOLATILE.is_dangerous is True
    
    def test_low_volatile_no_long(self):
        assert MarketRegime.LOW_VOLATILE.allow_long is False
    
    def test_low_volatile_not_dangerous(self):
        assert MarketRegime.LOW_VOLATILE.is_dangerous is False


class TestOrderStatus:
    def test_pending_is_active(self):
        assert OrderStatus.PENDING.is_active is True
    
    def test_filled_is_terminal(self):
        assert OrderStatus.FILLED.is_terminal is True
    
    def test_partial_filled_is_active(self):
        assert OrderStatus.PARTIAL_FILLED.is_active is True
    
    def test_cancelled_is_terminal(self):
        assert OrderStatus.CANCELLED.is_terminal is True


class TestOHLCV:
    def test_valid_ohlcv(self):
        data = OHLCV(
            symbol="BTC/USDT", date="2024-01-01",
            open=50000, high=51000, low=49000, close=50500, volume=1000
        )
        assert data.symbol == "BTC/USDT"
        assert data.data_quality == 1.0
    
    def test_invalid_high_lower_than_open(self):
        with pytest.raises(ValueError):
            OHLCV(
                symbol="BTC/USDT", date="2024-01-01",
                open=50000, high=48000, low=47000, close=49000, volume=1000
            )
    
    def test_invalid_low_higher_than_close(self):
        with pytest.raises(ValueError):
            OHLCV(
                symbol="BTC/USDT", date="2024-01-01",
                open=50000, high=51000, low=52000, close=50500, volume=1000
            )
    
    def test_zero_price_rejected(self):
        with pytest.raises(ValueError):
            OHLCV(
                symbol="BTC/USDT", date="2024-01-01",
                open=0, high=0, low=0, close=0, volume=1000
            )


class TestOnchainNetflow:
    def test_valid_netflow(self):
        data = OnchainNetflow(
            date="2024-01-01", netflow=-500.0, source="GLASSNODE"
        )
        assert data.netflow == -500.0
        assert data.data_quality == 1.0


class TestStablecoinSupply:
    def test_valid_supply(self):
        data = StablecoinSupply(
            date="2024-01-01",
            usdt_supply=80000000000,
            usdc_supply=30000000000,
            total_supply=110000000000
        )
        assert data.total_supply == 110000000000
    
    def test_mismatch_total(self):
        with pytest.raises(ValueError):
            StablecoinSupply(
                date="2024-01-01",
                usdt_supply=80000000000,
                usdc_supply=30000000000,
                total_supply=99999999999
            )


class TestFearGreedIndex:
    def test_extreme_fear(self):
        data = FearGreedIndex(date="2024-01-01", value=10, classification="Extreme Fear")
        assert data.classification == "Extreme Fear"
    
    def test_invalid_classification(self):
        with pytest.raises(ValueError):
            FearGreedIndex(date="2024-01-01", value=10, classification="Extreme Greed")


class TestPosition:
    def test_valid_position(self):
        pos = Position(
            symbol="BTC/USDT", entry_price=50000, amount=0.1,
            stop_price=48000, status=PositionStatus.OPEN,
            entry_time="2024-01-01T00:00:00"
        )
        assert pos.stop_price < pos.entry_price
    
    def test_invalid_stop_price(self):
        with pytest.raises(ValueError):
            Position(
                symbol="BTC/USDT", entry_price=50000, amount=0.1,
                stop_price=51000, status=PositionStatus.OPEN,
                entry_time="2024-01-01T00:00:00"
            )


class TestOrder:
    def test_limit_order_requires_price(self):
        with pytest.raises(ValueError):
            Order(
                order_id="123", symbol="BTC/USDT",
                side="buy", order_type="limit",
                amount=0.1, status=OrderStatus.PENDING
            )
    
    def test_market_order_no_price_needed(self):
        order = Order(
            order_id="123", symbol="BTC/USDT",
            side="buy", order_type="market",
            amount=0.1, status=OrderStatus.PENDING
        )
        assert order.price is None


class TestAccountEquity:
    def test_valid_equity(self):
        eq = AccountEquity(
            date="2024-01-01", equity=10000, cash=5000,
            position_value=5000, max_equity=10000, drawdown=0
        )
        assert eq.equity == eq.cash + eq.position_value
    
    def test_mismatch_equity(self):
        eq = AccountEquity(
            date="2024-01-01", equity=99999, cash=5000,
            position_value=4000, max_equity=10000, drawdown=0
        )
        assert eq.equity == 99999


class TestDataQuality:
    def test_fresh_data(self):
        dq = DataQuality(
            source="OKX", data_date="2024-01-01",
            current_date="2024-01-01",
            delay_days=0, quality_score=1.0, is_fresh=True
        )
        assert dq.is_usable is True
    
    def test_stale_data(self):
        dq = DataQuality(
            source="GLASSNODE", data_date="2024-01-01",
            current_date="2024-01-04",
            delay_days=3, quality_score=0.5, is_fresh=False
        )
        assert dq.is_usable is False
