"""
熔断状态检查器
检查当前是否处于熔断暂停期
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.repository import DataRepository
from ..models.schemas import CircuitBreakerEvent
from ..models.enums import CircuitBreakerType

logger = logging.getLogger("aosft")


class CircuitBreakerChecker:
    def __init__(self, repo: DataRepository):
        self.repo = repo
        self._cached_status: Optional[dict] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 60
    
    def check_circuit_breaker_status(self) -> dict:
        now = datetime.now()
        
        if (self._cached_status and self._cache_time
                and (now - self._cache_time).seconds < self._cache_ttl):
            return self._cached_status
        
        active_breaker = self.repo.get_active_circuit_breaker()
        
        if active_breaker is None:
            self._cached_status = {
                'is_active': False,
                'breaker_type': None,
                'recovery_stage': 0,
                'allowed_position_ratio': 1.0,
                'message': '系统正常运行'
            }
        else:
            trigger_time = datetime.fromisoformat(active_breaker['trigger_time'])
            days_since_trigger = (now - trigger_time).days
            
            stage1_days = int(self.repo.get_config('recovery_stage1_days') or '10')
            stage2_days = int(self.repo.get_config('recovery_stage2_days') or '20')
            
            if days_since_trigger >= stage2_days:
                recovery_stage = 2
                allowed_ratio = 1.0
                message = f'熔断恢复完成(触发{days_since_trigger}天≥{stage2_days}天)'
            elif days_since_trigger >= stage1_days:
                recovery_stage = 1
                allowed_ratio = 0.5
                message = f'熔断分级恢复中(触发{days_since_trigger}天≥{stage1_days}天)，允许50%仓位'
            else:
                recovery_stage = 0
                allowed_ratio = 0.0
                message = f'熔断暂停中(触发{days_since_trigger}天<{stage1_days}天)，禁止交易'
            
            self._cached_status = {
                'is_active': recovery_stage < 2,
                'breaker_type': active_breaker['breaker_type'],
                'trigger_time': active_breaker['trigger_time'],
                'days_since_trigger': days_since_trigger,
                'recovery_stage': recovery_stage,
                'allowed_position_ratio': allowed_ratio,
                'message': message
            }
        
        self._cache_time = now
        return self._cached_status
    
    def get_circuit_breaker_info(self) -> Optional[dict]:
        return self.repo.get_active_circuit_breaker()
    
    def is_trading_allowed(self) -> tuple[bool, float, str]:
        status = self.check_circuit_breaker_status()
        if not status['is_active']:
            return True, 1.0, '正常交易'
        return (
            status['allowed_position_ratio'] > 0,
            status['allowed_position_ratio'],
            status['message']
        )
    
    def invalidate_cache(self):
        self._cached_status = None
        self._cache_time = None
