"""
稳定币和情绪指数数据接口
"""
import logging
import requests
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger("aosft")


class CoinGeckoInterface:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_stablecoin_supply(
        self,
        days: int = 30
    ) -> List[dict]:
        try:
            results = []
            
            for coin_id, name in [('tether', 'USDT'), ('usd-coin', 'USDC')]:
                resp = self.session.get(
                    f"{self.BASE_URL}/coins/{coin_id}/market_chart",
                    params={
                        'vs_currency': 'usd',
                        'days': days,
                        'interval': 'daily'
                    },
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get('market_caps', []):
                    timestamp_ms, value = item
                    date = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
                    
                    existing = next((r for r in results if r['date'] == date), None)
                    if existing:
                        existing[f'{name.lower()}_supply'] = value
                    else:
                        entry = {'date': date, 'usdt_supply': 0, 'usdc_supply': 0}
                        entry[f'{name.lower()}_supply'] = value
                        results.append(entry)
            
            for r in results:
                r['total_supply'] = r['usdt_supply'] + r['usdc_supply']
            
            results.sort(key=lambda x: x['date'])
            logger.info(f"获取稳定币供应数据{len(results)}条")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API调用失败: {e}")
            raise
    
    def close(self):
        self.session.close()


class FearGreedInterface:
    BASE_URL = "https://api.alternative.me/fng/"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_fear_greed_index(
        self,
        limit: int = 30
    ) -> List[dict]:
        try:
            resp = self.session.get(
                self.BASE_URL,
                params={'limit': limit, 'format': 'json'},
                timeout=self.timeout
            )
            resp.raise_for_status()
            
            data = resp.json().get('data', [])
            results = []
            
            for item in data:
                date = datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d')
                results.append({
                    'date': date,
                    'value': int(item['value']),
                    'classification': item['value_classification']
                })
            
            results.sort(key=lambda x: x['date'])
            logger.info(f"获取恐惧贪婪指数{len(results)}条")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"alternative.me API调用失败: {e}")
            raise
    
    def close(self):
        self.session.close()


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        self.session = requests.Session()
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.debug("Telegram未配置，跳过通知")
            return False
        
        try:
            resp = self.session.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': parse_mode
                },
                timeout=self.timeout
            )
            resp.raise_for_status()
            logger.debug("Telegram消息发送成功")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram消息发送失败: {e}")
            return False
    
    def notify_trade(self, action: str, symbol: str, amount: float, price: float, **kwargs):
        msg = (
            f"📊 <b>交易信号</b>\n"
            f"动作: {action}\n"
            f"标的: {symbol}\n"
            f"数量: {amount:.8f}\n"
            f"价格: ${price:,.2f}\n"
        )
        if kwargs.get('reason'):
            msg += f"原因: {kwargs['reason']}\n"
        self.send_message(msg)
    
    def notify_alert(self, alert_type: str, message: str, severity: str = "WARNING"):
        emoji = {"WARNING": "⚠️", "ERROR": "🚨", "INFO": "ℹ️"}.get(severity, "📢")
        msg = f"{emoji} <b>[{alert_type}]</b>\n{message}"
        self.send_message(msg)
    
    def notify_daily_report(self, equity: float, position: Optional[dict] = None, drawdown: float = 0):
        msg = (
            f"📈 <b>每日报告</b>\n"
            f"净值: ${equity:,.2f}\n"
            f"回撤: {drawdown*100:.2f}%\n"
        )
        if position:
            msg += f"持仓: {position.get('amount', 0):.8f} BTC\n"
        else:
            msg += "持仓: 空仓\n"
        self.send_message(msg)
    
    def close(self):
        self.session.close()
