"""
市场异常检查器
检查市场是否出现异常波动
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.repository import DataRepository

logger = logging.getLogger("aosft")


class MarketAnomalyChecker:
    def __init__(self, repo: DataRepository):
        self.repo = repo
    
    def check_market_anomaly(self) -> dict:
        latest = self.repo.get_latest_ohlcv()
        if not latest:
            return {'is_anomaly': False, 'reason': '无行情数据'}
        
        daily_volatility = (latest['high'] - latest['low']) / latest['open']
        is_high_volatility = daily_volatility > 0.10
        
        result = {
            'date': latest['date'],
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'daily_volatility': round(daily_volatility, 4),
            'is_high_volatility': is_high_volatility,
            'anomalies': []
        }
        
        if is_high_volatility:
            result['anomalies'].append({
                'type': 'HIGH_DAILY_VOLATILITY',
                'value': round(daily_volatility * 100, 2),
                'threshold': 10.0,
                'unit': '%'
            })
        
        ohlcv_list = self.repo.load_ohlcv(start_date=None, limit=2)
        if len(ohlcv_list) >= 2:
            prev = ohlcv_list[-2]
            price_change_24h = (latest['close'] - prev['close']) / prev['close']
            
            if price_change_24h <= -0.15:
                result['anomalies'].append({
                    'type': 'CRASH_24H',
                    'value': round(price_change_24h * 100, 2),
                    'threshold': -15.0,
                    'unit': '%'
                })
        
        result['is_anomaly'] = len(result['anomalies']) > 0
        if result['is_anomaly']:
            logger.warning(
                f"[MARKET-ANOMALY] 检测到{len(result['anomalies'])}个市场异常: "
                f"{[a['type'] for a in result['anomalies']]}"
            )
        
        return result
    
    def get_anomaly_details(self) -> Optional[dict]:
        result = self.check_market_anomaly()
        if result['is_anomaly']:
            return result
        return None
    
    def should_halt_trading(self) -> tuple[bool, str]:
        result = self.check_market_anomaly()
        
        for anomaly in result.get('anomalies', []):
            if anomaly['type'] == 'CRASH_24H':
                return True, f"24小时跌幅{anomaly['value']}%≤-15%，建议暂停交易"
            if anomaly['type'] == 'HIGH_DAILY_VOLATILITY':
                position = self.repo.load_current_position()
                if position:
                    entry_price = position['entry_price']
                    current_price = result.get('close', 0)
                    if current_price < entry_price:
                        loss_pct = (entry_price - current_price) / entry_price
                        if loss_pct > 0.08:
                            return True, f"异常波动且浮亏{round(loss_pct*100,2)}%>8%"
        
        return False, "市场正常"
