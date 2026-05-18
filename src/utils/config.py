"""
配置管理模块
从环境变量和配置文件加载配置
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from dotenv import load_dotenv


load_dotenv()


def mask_api_key(key: str, visible_chars: int = 8) -> str:
    if not key or len(key) <= visible_chars:
        return "***"
    return f"{key[:visible_chars]}***"


class APIConfig(BaseModel):
    okx_api_key: str = Field(..., description="OKX API Key")
    okx_secret: str = Field(..., description="OKX Secret Key")
    okx_password: str = Field(..., description="OKX Password")
    glassnode_api_key: Optional[str] = Field(None, description="Glassnode API Key")
    cryptoquant_api_key: Optional[str] = Field(None, description="CryptoQuant API Key")
    telegram_bot_token: Optional[str] = Field(None, description="Telegram Bot Token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram Chat ID")
    
    @field_validator('okx_api_key', 'okx_secret', 'okx_password')
    @classmethod
    def validate_okx_credentials(cls, v):
        if not v or v == 'your_api_key_here':
            raise ValueError("OKX API凭证未配置，请检查.env文件")
        return v
    
    def get_masked_credentials(self) -> dict:
        return {
            'okx_api_key': mask_api_key(self.okx_api_key),
            'okx_secret': mask_api_key(self.okx_secret),
            'okx_password': mask_api_key(self.okx_password),
            'glassnode_api_key': mask_api_key(self.glassnode_api_key) if self.glassnode_api_key else None,
        }


class StrategyConfig(BaseModel):
    ma_period: int = Field(20, description="趋势均线周期", gt=0)
    atr_period: int = Field(14, description="ATR计算周期", gt=0)
    atr_ma_period: int = Field(30, description="ATR均值周期", gt=0)
    netflow_ma_days: int = Field(7, description="净流入平滑天数", gt=0)
    stable_change_days: int = Field(7, description="稳定币变化统计天数", gt=0)
    netflow_confirm_days: int = Field(3, description="连续满足平仓信号的天数", gt=0)
    stable_confirm_days: int = Field(3, description="稳定币连续天数", gt=0)
    stop_atr_multiplier: float = Field(2.0, description="止损ATR倍数", gt=0)
    position_ratio: float = Field(0.5, description="仓位占比", gt=0, le=1.0)
    max_loss_per_trade: float = Field(0.05, description="单笔最大亏损占比", gt=0, le=1.0)
    max_drawdown_global: float = Field(0.20, description="全局最大回撤熔断", gt=0, le=1.0)
    fear_greed_ceiling: int = Field(80, description="情绪过热不开仓阈值", ge=0, le=100)
    
    @field_validator('position_ratio', 'max_loss_per_trade', 'max_drawdown_global')
    @classmethod
    def validate_ratio(cls, v):
        if not 0 < v <= 1:
            raise ValueError(f"比例值必须在(0, 1]范围内")
        return v


class DataQualityConfig(BaseModel):
    freshness_threshold: int = Field(3, description="数据新鲜度阈值（天）", gt=0)
    quality_full_threshold: int = Field(1, description="数据质量满分阈值（天）", gt=0)
    quality_downgrade_threshold: int = Field(2, description="数据质量降权阈值（天）", gt=0)


class OrderConfig(BaseModel):
    limit_order_timeout: int = Field(300, description="限价单超时时间（秒）", gt=0)
    max_order_timeout: int = Field(1800, description="订单最大超时时间（秒）", gt=0)
    slippage_tolerance: float = Field(0.002, description="滑点容忍", gt=0, le=0.1)


class RecoveryConfig(BaseModel):
    stage1_days: int = Field(10, description="分级恢复第一阶段天数", gt=0)
    stage2_days: int = Field(20, description="分级恢复第二阶段天数", gt=0)
    stage1_position_ratio: float = Field(0.5, description="第一阶段仓位比例", gt=0, le=1.0)


class Config(BaseModel):
    api: APIConfig
    strategy: StrategyConfig
    data_quality: DataQualityConfig
    order: OrderConfig
    recovery: RecoveryConfig
    database_path: str = Field("data/aosft.db", description="数据库路径")
    log_level: str = Field("INFO", description="日志级别")
    log_dir: str = Field("logs", description="日志目录")
    
    @classmethod
    def load(cls) -> 'Config':
        api_config = APIConfig(
            okx_api_key=os.getenv('OKX_API_KEY', ''),
            okx_secret=os.getenv('OKX_SECRET', ''),
            okx_password=os.getenv('OKX_PASSWORD', ''),
            glassnode_api_key=os.getenv('GLASSNODE_API_KEY'),
            cryptoquant_api_key=os.getenv('CRYPTOQUANT_API_KEY'),
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        )
        
        strategy_config = StrategyConfig(
            ma_period=int(os.getenv('MA_PERIOD', '20')),
            atr_period=int(os.getenv('ATR_PERIOD', '14')),
            atr_ma_period=int(os.getenv('ATR_MA_PERIOD', '30')),
            netflow_ma_days=int(os.getenv('NETFLOW_MA_DAYS', '7')),
            stable_change_days=int(os.getenv('STABLE_CHANGE_DAYS', '7')),
            netflow_confirm_days=int(os.getenv('NETFLOW_CONFIRM_DAYS', '3')),
            stable_confirm_days=int(os.getenv('STABLE_CONFIRM_DAYS', '3')),
            stop_atr_multiplier=float(os.getenv('STOP_ATR_MULTIPLIER', '2.0')),
            position_ratio=float(os.getenv('POSITION_RATIO', '0.5')),
            max_loss_per_trade=float(os.getenv('MAX_LOSS_PER_TRADE', '0.05')),
            max_drawdown_global=float(os.getenv('MAX_DRAWDOWN_GLOBAL', '0.20')),
            fear_greed_ceiling=int(os.getenv('FEAR_GREED_CEILING', '80')),
        )
        
        data_quality_config = DataQualityConfig(
            freshness_threshold=int(os.getenv('DATA_FRESHNESS_THRESHOLD', '3')),
            quality_full_threshold=int(os.getenv('DATA_QUALITY_FULL_THRESHOLD', '1')),
            quality_downgrade_threshold=int(os.getenv('DATA_QUALITY_DOWNGRADE_THRESHOLD', '2')),
        )
        
        order_config = OrderConfig(
            limit_order_timeout=int(os.getenv('LIMIT_ORDER_TIMEOUT', '300')),
            max_order_timeout=int(os.getenv('MAX_ORDER_TIMEOUT', '1800')),
        )
        
        recovery_config = RecoveryConfig(
            stage1_days=int(os.getenv('RECOVERY_STAGE1_DAYS', '10')),
            stage2_days=int(os.getenv('RECOVERY_STAGE2_DAYS', '20')),
        )
        
        return cls(
            api=api_config,
            strategy=strategy_config,
            data_quality=data_quality_config,
            order=order_config,
            recovery=recovery_config,
            database_path=os.getenv('DATABASE_PATH', 'data/aosft.db'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_dir=os.getenv('LOG_DIR', 'logs'),
        )
    
    def validate_required_configs(self) -> list:
        missing = []
        if not self.api.okx_api_key or self.api.okx_api_key == 'your_api_key_here':
            missing.append('OKX_API_KEY')
        if not self.api.okx_secret or self.api.okx_secret == 'your_secret_key_here':
            missing.append('OKX_SECRET')
        if not self.api.okx_password or self.api.okx_password == 'your_password_here':
            missing.append('OKX_PASSWORD')
        return missing
