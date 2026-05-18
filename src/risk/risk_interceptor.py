"""
风控前置拦截器
在交易信号执行前进行风控检查，拥有"一票否决权"
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.repository import DataRepository
from ..models.schemas import RiskInterception, TradeSignal
from ..models.enums import SignalType, InterceptionType
from .circuit_breaker_checker import CircuitBreakerChecker
from .data_freshness_checker import DataFreshnessChecker
from .market_anomaly_checker import MarketAnomalyChecker

logger = logging.getLogger("aosft")


class RiskInterceptor:
    def __init__(self, repo: DataRepository, stale_threshold: int = 3):
        self.repo = repo
        self.circuit_checker = CircuitBreakerChecker(repo)
        self.freshness_checker = DataFreshnessChecker(repo, stale_threshold)
        self.anomaly_checker = MarketAnomalyChecker(repo)
    
    def intercept(self, signal: Optional[TradeSignal] = None) -> dict:
        result = {
            'passed': True,
            'interceptions': [],
            'action': 'ALLOW',
            'position_ratio_override': None,
            'reason': ''
        }
        
        breaker_result = self._check_circuit_breaker()
        if not breaker_result['passed']:
            result['passed'] = False
            result['interceptions'].append(breaker_result)
            if breaker_result.get('position_ratio') is not None:
                result['position_ratio_override'] = breaker_result['position_ratio']
        
        freshness_result = self._check_data_freshness()
        if not freshness_result['passed']:
            result['passed'] = False
            result['interceptions'].append(freshness_result)
        
        if signal and signal.signal_type == SignalType.OPEN:
            anomaly_result = self._check_market_anomaly()
            if not anomaly_result['passed']:
                result['interceptions'].append(anomaly_result)
                if anomaly_result.get('force_close'):
                    result['action'] = 'FORCE_CLOSE'
                else:
                    result['passed'] = False
        
        if not result['passed']:
            result['action'] = 'BLOCK'
            result['reason'] = '; '.join(
                i['reason'] for i in result['interceptions']
            )
            logger.warning(
                f"[RISK-INTERCEPT] 信号被拦截: action={result['action']} "
                f"reason={result['reason']}"
            )
            
            self._save_interception(signal, result)
        
        return result
    
    def _check_circuit_breaker(self) -> dict:
        allowed, ratio, msg = self.circuit_checker.is_trading_allowed()
        
        if not allowed:
            return {
                'passed': False,
                'type': InterceptionType.CIRCUIT_BREAKER,
                'reason': msg,
                'position_ratio': ratio
            }
        
        if ratio < 1.0:
            return {
                'passed': True,
                'type': InterceptionType.CIRCUIT_BREAKER,
                'reason': msg,
                'position_ratio': ratio
            }
        
        return {'passed': True, 'reason': '熔断状态正常'}
    
    def _check_data_freshness(self) -> dict:
        fresh, msg = self.freshness_checker.is_critical_data_fresh()
        
        if not fresh:
            return {
                'passed': False,
                'type': InterceptionType.DATA_STALE,
                'reason': msg
            }
        
        return {'passed': True, 'reason': '数据新鲜度正常'}
    
    def _check_market_anomaly(self) -> dict:
        should_halt, msg = self.anomaly_checker.should_halt_trading()
        
        if should_halt:
            return {
                'passed': False,
                'type': InterceptionType.MARKET_ANOMALY,
                'reason': msg,
                'force_close': '浮亏' in msg or '跌幅' in msg
            }
        
        return {'passed': True, 'reason': '市场状态正常'}
    
    def _save_interception(self, signal: Optional[TradeSignal], result: dict):
        primary = result['interceptions'][0] if result['interceptions'] else {}
        
        interception = RiskInterception(
            timestamp=datetime.now().isoformat(),
            interception_type=primary.get('type', InterceptionType.MANUAL),
            signal_type=signal.signal_type if signal else None,
            reason=result['reason'],
            action_taken=result['action'],
            metadata=str(result['interceptions'])
        )
        
        self.repo.save_interception(interception)
    
    def quick_check(self) -> bool:
        allowed, _, _ = self.circuit_checker.is_trading_allowed()
        if not allowed:
            return False
        
        fresh, _ = self.freshness_checker.is_critical_data_fresh()
        return fresh
