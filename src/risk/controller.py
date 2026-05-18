"""
风险控制核心模块
硬止损、闪崩保护、熔断机制
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.schemas import CircuitBreakerEvent, Position, TradeSignal
from ..models.enums import SignalType, CircuitBreakerType, PositionStatus
from ..models.repository import DataRepository
from ..collectors.okx_interface import OKXMarketInterface
from ..signals.generator import SignalGenerator

logger = logging.getLogger("aosft")


class HardStopLoss:
    def __init__(self, repo: DataRepository):
        self.repo = repo
    
    def check_stop_trigger(self) -> Optional[TradeSignal]:
        position = self.repo.load_current_position()
        if not position:
            return None
        
        latest = self.repo.get_latest_ohlcv()
        if not latest:
            return None
        
        current_price = latest['close']
        stop_price = position['stop_price']
        
        if current_price <= stop_price:
            logger.warning(
                f"[STOP-LOSS] 硬止损触发! "
                f"current={current_price:.2f} stop={stop_price:.2f} "
                f"entry={position['entry_price']:.2f}"
            )
            
            signal_gen = SignalGenerator()
            return signal_gen.generate_forced_close_signal(
                price=current_price,
                reason=f"硬止损: 价格{current_price:.2f}≤止损价{stop_price:.2f}"
            )
        
        return None
    
    def update_stop_price(self, entry_price: float, atr: float,
                          current_stop: float, multiplier: float = 2.0) -> float:
        new_stop = entry_price - multiplier * atr
        updated_stop = max(current_stop, new_stop)
        
        if updated_stop > current_stop:
            logger.info(
                f"[STOP-LOSS] 止损价上移: "
                f"{current_stop:.2f} → {updated_stop:.2f}"
            )
        
        return updated_stop


class FlashCrashProtector:
    def __init__(self, repo: DataRepository, market_interface: OKXMarketInterface):
        self.repo = repo
        self.market = market_interface
        self._last_check_price: Optional[float] = None
        self._last_check_time: Optional[datetime] = None
    
    def check_flash_crash(self) -> Optional[TradeSignal]:
        try:
            ticker = self.market.fetch_ticker("BTC/USDT")
            current_price = ticker.get('last', 0)
            now = datetime.now()
            
            if self._last_check_price and self._last_check_time:
                elapsed_minutes = (now - self._last_check_time).total_seconds() / 60
                
                if elapsed_minutes <= 15:
                    drop_pct = (self._last_check_price - current_price) / self._last_check_price
                    
                    if drop_pct >= 0.05:
                        logger.warning(
                            f"[FLASH-CRASH] 闪崩检测! "
                            f"15分钟内跌幅{drop_pct*100:.2f}%≥5%"
                        )
                        
                        signal_gen = SignalGenerator()
                        return signal_gen.generate_forced_close_signal(
                            price=current_price,
                            reason=f"闪崩保护: 15分钟跌幅{drop_pct*100:.2f}%≥5%"
                        )
            
            self._last_check_price = current_price
            self._last_check_time = now
            return None
            
        except Exception as e:
            logger.error(f"闪崩监控异常: {e}")
            return None


class CircuitBreakerManager:
    def __init__(self, repo: DataRepository, max_drawdown: float = 0.20):
        self.repo = repo
        self.max_drawdown = max_drawdown
        self._is_active = False
        self._trigger_time: Optional[datetime] = None
    
    def check_global_drawdown(self) -> Optional[CircuitBreakerEvent]:
        equity = self.repo.get_latest_equity()
        if not equity:
            return None
        
        drawdown = equity.get('drawdown', 0)
        
        if drawdown >= self.max_drawdown:
            logger.warning(
                f"[CIRCUIT-BREAKER] 全局回撤熔断触发! "
                f"drawdown={drawdown*100:.2f}%≥{self.max_drawdown*100:.2f}%"
            )
            
            event = CircuitBreakerEvent(
                trigger_time=datetime.now().isoformat(),
                breaker_type=CircuitBreakerType.GLOBAL_DRAWDOWN,
                trigger_value=drawdown,
                threshold=self.max_drawdown
            )
            
            self.repo.save_circuit_breaker_event(event)
            self._is_active = True
            self._trigger_time = datetime.now()
            
            return event
        
        return None
    
    def check_black_swan(self, price_change_24h: float) -> Optional[CircuitBreakerEvent]:
        if price_change_24h <= -0.15:
            logger.warning(
                f"[CIRCUIT-BREAKER] 黑天鹅熔断触发! "
                f"24h跌幅={price_change_24h*100:.2f}%≤-15%"
            )
            
            event = CircuitBreakerEvent(
                trigger_time=datetime.now().isoformat(),
                breaker_type=CircuitBreakerType.BLACK_SWAN,
                trigger_value=price_change_24h,
                threshold=-0.15
            )
            
            self.repo.save_circuit_breaker_event(event)
            self._is_active = True
            self._trigger_time = datetime.now()
            
            return event
        
        return None
    
    def check_abnormal_volatility(
        self,
        daily_volatility: float,
        floating_loss_pct: float
    ) -> Optional[CircuitBreakerEvent]:
        if daily_volatility > 0.10 and floating_loss_pct > 0.08:
            logger.warning(
                f"[CIRCUIT-BREAKER] 异常波动熔断触发! "
                f"volatility={daily_volatility*100:.2f}% loss={floating_loss_pct*100:.2f}%"
            )
            
            event = CircuitBreakerEvent(
                trigger_time=datetime.now().isoformat(),
                breaker_type=CircuitBreakerType.ABNORMAL_VOLATILITY,
                trigger_value=daily_volatility,
                threshold=0.10
            )
            
            self.repo.save_circuit_breaker_event(event)
            return event
        
        return None
    
    def force_close_on_circuit_breaker(self, event: CircuitBreakerEvent) -> Optional[TradeSignal]:
        position = self.repo.load_current_position()
        if not position:
            return None
        
        latest = self.repo.get_latest_ohlcv()
        if not latest:
            return None
        
        signal_gen = SignalGenerator()
        return signal_gen.generate_forced_close_signal(
            price=latest['close'],
            reason=f"熔断强制平仓: {event.breaker_type.value}"
        )
    
    def manual_recovery(self) -> bool:
        if not self._is_active:
            return False
        
        logger.info("[CIRCUIT-BREAKER] 人工恢复熔断")
        self._is_active = False
        self._trigger_time = None
        return True


class RiskController:
    def __init__(self, repo: DataRepository, config, market_interface: OKXMarketInterface):
        self.repo = repo
        self.config = config
        self.hard_stop = HardStopLoss(repo)
        self.flash_crash = FlashCrashProtector(repo, market_interface)
        self.circuit_breaker = CircuitBreakerManager(
            repo, config.strategy.max_drawdown_global
        )
    
    def run_risk_check(self) -> list:
        actions = []
        
        stop_signal = self.hard_stop.check_stop_trigger()
        if stop_signal:
            actions.append(('hard_stop', stop_signal))
        
        drawdown_event = self.circuit_breaker.check_global_drawdown()
        if drawdown_event:
            close_signal = self.circuit_breaker.force_close_on_circuit_breaker(drawdown_event)
            if close_signal:
                actions.append(('circuit_breaker', close_signal))
        
        return actions
    
    def run_flash_crash_check(self) -> Optional[TradeSignal]:
        return self.flash_crash.check_flash_crash()
