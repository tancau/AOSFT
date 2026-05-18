"""
Pydantic数据模型定义
定义所有数据结构的验证模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from .enums import (
    MarketRegime, SignalType, PositionStatus, OrderStatus, 
    OrderSide, OrderType, DataSource, CircuitBreakerType, InterceptionType
)


class OHLCV(BaseModel):
    symbol: str = Field(..., description="交易对")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    open: float = Field(..., gt=0, description="开盘价")
    high: float = Field(..., gt=0, description="最高价")
    low: float = Field(..., gt=0, description="最低价")
    close: float = Field(..., gt=0, description="收盘价")
    volume: float = Field(..., ge=0, description="交易量")
    collected_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_quality: float = Field(default=1.0, ge=0, le=1.0, description="数据质量评分")
    
    @model_validator(mode='after')
    def validate_price_range(self):
        if self.high < max(self.open, self.close):
            raise ValueError(f"最高价{self.high}不能小于开盘价{self.open}和收盘价{self.close}的最大值")
        if self.low > min(self.open, self.close):
            raise ValueError(f"最低价{self.low}不能大于开盘价{self.open}和收盘价{self.close}的最小值")
        return self


class OnchainNetflow(BaseModel):
    date: str = Field(..., description="日期")
    netflow: float = Field(..., description="净流入量")
    source: DataSource = Field(..., description="数据源")
    collected_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_freshness: int = Field(default=0, ge=0, description="数据新鲜度(天)")
    data_quality: float = Field(default=1.0, ge=0, le=1.0)


class StablecoinSupply(BaseModel):
    date: str = Field(..., description="日期")
    usdt_supply: float = Field(..., gt=0, description="USDT供应量")
    usdc_supply: float = Field(..., gt=0, description="USDC供应量")
    total_supply: float = Field(..., gt=0, description="总供应量")
    change_7d: Optional[float] = Field(None, description="7日变化率")
    collected_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_quality: float = Field(default=1.0, ge=0, le=1.0)
    
    @field_validator('total_supply')
    @classmethod
    def validate_total(cls, v, info):
        if 'usdt_supply' in info.data and 'usdc_supply' in info.data:
            expected = info.data['usdt_supply'] + info.data['usdc_supply']
            if abs(v - expected) / expected > 0.01:
                raise ValueError(f"总供应量{v}与USDT+USDC{expected}不匹配")
        return v


class FearGreedIndex(BaseModel):
    date: str = Field(..., description="日期")
    value: int = Field(..., ge=0, le=100, description="恐惧贪婪指数值")
    classification: str = Field(..., description="分类")
    collected_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('classification')
    @classmethod
    def validate_classification(cls, v, info):
        if 'value' in info.data:
            value = info.data['value']
            expected = cls._get_classification(value)
            if v != expected:
                v = expected
        return v
    
    @staticmethod
    def _get_classification(value: int) -> str:
        if value <= 25:
            return "Extreme Fear"
        elif value <= 45:
            return "Fear"
        elif value <= 55:
            return "Neutral"
        elif value <= 75:
            return "Greed"
        else:
            return "Extreme Greed"


class TradeSignal(BaseModel):
    timestamp: str = Field(..., description="时间戳")
    signal_type: SignalType = Field(..., description="信号类型")
    symbol: str = Field(..., description="交易对")
    price: float = Field(..., gt=0, description="信号价格")
    regime: MarketRegime = Field(..., description="市场体制")
    netflow_condition: bool = Field(..., description="净流入条件")
    stable_condition: bool = Field(..., description="稳定币条件")
    fg_condition: bool = Field(..., description="情绪条件")
    reason: Optional[str] = Field(None, description="信号原因")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Position(BaseModel):
    symbol: str = Field(..., description="交易对")
    entry_price: float = Field(..., gt=0, description="入场价格")
    amount: float = Field(..., gt=0, description="持仓数量")
    stop_price: float = Field(..., gt=0, description="止损价格")
    status: PositionStatus = Field(..., description="持仓状态")
    entry_time: str = Field(..., description="入场时间")
    exit_price: Optional[float] = Field(None, description="离场价格")
    exit_time: Optional[str] = Field(None, description="离场时间")
    exit_reason: Optional[str] = Field(None, description="离场原因")
    pnl: Optional[float] = Field(None, description="盈亏")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @model_validator(mode='after')
    def validate_stop_price(self):
        if self.stop_price >= self.entry_price:
            raise ValueError(f"止损价格{self.stop_price}必须小于入场价格{self.entry_price}")
        return self


class AccountEquity(BaseModel):
    date: str = Field(..., description="日期")
    equity: float = Field(..., ge=0, description="总净值")
    cash: float = Field(..., ge=0, description="现金")
    position_value: float = Field(..., ge=0, description="持仓价值")
    daily_pnl: Optional[float] = Field(None, description="当日盈亏")
    total_pnl: Optional[float] = Field(None, description="累计盈亏")
    max_equity: float = Field(..., gt=0, description="历史最高净值")
    drawdown: float = Field(..., ge=0, le=1, description="回撤率")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('equity')
    @classmethod
    def validate_equity(cls, v, info):
        if 'cash' in info.data and 'position_value' in info.data:
            expected = info.data['cash'] + info.data['position_value']
            if abs(v - expected) / expected > 0.01:
                raise ValueError(f"总净值{v}与现金+持仓价值{expected}不匹配")
        return v


class Order(BaseModel):
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="交易对")
    side: OrderSide = Field(..., description="买卖方向")
    order_type: OrderType = Field(..., description="订单类型")
    amount: float = Field(..., gt=0, description="订单数量")
    price: Optional[float] = Field(None, description="限价单价格")
    status: OrderStatus = Field(..., description="订单状态")
    filled_amount: float = Field(default=0, ge=0, description="已成交数量")
    avg_price: Optional[float] = Field(None, description="平均成交价")
    fee: float = Field(default=0, description="手续费")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    timeout_at: Optional[str] = Field(None, description="超时时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    @model_validator(mode='after')
    def validate_limit_price(self):
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("限价单必须指定价格")
        return self


class RiskInterception(BaseModel):
    timestamp: str = Field(..., description="时间戳")
    interception_type: InterceptionType = Field(..., description="拦截类型")
    signal_type: Optional[SignalType] = Field(None, description="被拦截的信号类型")
    reason: str = Field(..., description="拦截原因")
    action_taken: str = Field(..., description="采取的动作")
    metadata: Optional[str] = Field(None, description="元数据")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class CircuitBreakerEvent(BaseModel):
    trigger_time: str = Field(..., description="触发时间")
    breaker_type: CircuitBreakerType = Field(..., description="熔断类型")
    trigger_value: float = Field(..., description="触发值")
    threshold: float = Field(..., description="阈值")
    recovery_stage: int = Field(default=0, ge=0, le=2, description="恢复阶段")
    recovery_start_time: Optional[str] = Field(None, description="恢复开始时间")
    recovery_end_time: Optional[str] = Field(None, description="恢复结束时间")
    manual_recovery: bool = Field(default=False, description="是否人工恢复")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class DataQuality(BaseModel):
    source: DataSource = Field(..., description="数据源")
    data_date: str = Field(..., description="数据日期")
    current_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    delay_days: int = Field(..., ge=0, description="延迟天数")
    quality_score: float = Field(..., ge=0, le=1, description="质量评分")
    is_fresh: bool = Field(..., description="是否新鲜")
    
    @property
    def is_usable(self) -> bool:
        return self.delay_days < 3
