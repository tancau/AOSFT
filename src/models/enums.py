"""
核心枚举定义
定义系统中使用的所有枚举类型
"""
from enum import Enum


class MarketRegime(str, Enum):
    BULL_VOLATILE = "BULL_VOLATILE"
    BEAR_VOLATILE = "BEAR_VOLATILE"
    LOW_VOLATILE = "LOW_VOLATILE"
    TRANSITIONING = "TRANSITIONING"
    
    @property
    def allow_long(self) -> bool:
        return self in (MarketRegime.BULL_VOLATILE, MarketRegime.TRANSITIONING)
    
    @property
    def is_dangerous(self) -> bool:
        return self == MarketRegime.BEAR_VOLATILE


class SignalType(str, Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    STOP_LOSS = "STOP_LOSS"
    FORCED_CLOSE = "FORCED_CLOSE"
    
    @property
    def is_close_signal(self) -> bool:
        return self in (SignalType.CLOSE, SignalType.STOP_LOSS, SignalType.FORCED_CLOSE)


class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class DataSource(str, Enum):
    GLASSNODE = "GLASSNODE"
    CRYPTOQUANT = "CRYPTOQUANT"
    COINMETRICS = "COINMETRICS"
    OKX = "OKX"
    COINGECKO = "COINGECKO"
    ALTERNATIVE_ME = "ALTERNATIVE_ME"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    
    @property
    def is_active(self) -> bool:
        return self in (OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED)
    
    @property
    def is_terminal(self) -> bool:
        return self in (OrderStatus.FILLED, OrderStatus.REJECTED, OrderStatus.CANCELLED)


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"


class CircuitBreakerType(str, Enum):
    GLOBAL_DRAWDOWN = "GLOBAL_DRAWDOWN"
    BLACK_SWAN = "BLACK_SWAN"
    FLASH_CRASH = "FLASH_CRASH"
    ABNORMAL_VOLATILITY = "ABNORMAL_VOLATILITY"


class InterceptionType(str, Enum):
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    DATA_STALE = "DATA_STALE"
    MARKET_ANOMALY = "MARKET_ANOMALY"
    RISK_LIMIT = "RISK_LIMIT"
    MANUAL = "MANUAL"


class MetricType(str, Enum):
    DATA_FRESHNESS = "DATA_FRESHNESS"
    STRATEGY_PERFORMANCE = "STRATEGY_PERFORMANCE"
    RISK_STATS = "RISK_STATS"
    API_STATS = "API_STATS"
