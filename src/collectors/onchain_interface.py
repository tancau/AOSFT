"""
链上数据接口封装
获取交易所BTC净流入等链上数据
"""
import logging
import requests
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger("aosft")


class GlassnodeInterface:
    BASE_URL = "https://api.glassnode.com/v1"
    
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_exchange_netflow(
        self,
        asset: str = "BTC",
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[dict]:
        if until is None:
            until = datetime.now().strftime("%Y-%m-%d")
        if since is None:
            since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            params = {
                'a': asset.lower(),
                'api_key': self.api_key,
                's': int(datetime.strptime(since, "%Y-%m-%d").timestamp()),
                'u': int(datetime.strptime(until, "%Y-%m-%d").timestamp()),
            }
            
            resp = self.session.get(
                f"{self.BASE_URL}/metrics/transactions/transfers_volume_exchanges_net",
                params=params,
                timeout=self.timeout
            )
            resp.raise_for_status()
            
            data = resp.json()
            results = []
            for item in data:
                date = datetime.fromtimestamp(item['t']).strftime('%Y-%m-%d')
                results.append({
                    'date': date,
                    'netflow': item['v'],
                    'source': 'GLASSNODE'
                })
            
            logger.info(f"获取Glassnode净流入数据{len(results)}条")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Glassnode API调用失败: {e}")
            raise
    
    def close(self):
        self.session.close()


class CryptoQuantInterface:
    BASE_URL = "https://api.cryptoquant.com/v1"
    
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def get_exchange_netflow(
        self,
        exchange: str = "all",
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[dict]:
        if until is None:
            until = datetime.now().strftime("%Y-%m-%d")
        if since is None:
            since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            params = {
                'from': since,
                'to': until,
                'exchange': exchange
            }
            
            resp = self.session.get(
                f"{self.BASE_URL}/btc/exchange-flows/net-flow",
                params=params,
                timeout=self.timeout
            )
            resp.raise_for_status()
            
            data = resp.json().get('result', {}).get('data', [])
            results = []
            for item in data:
                results.append({
                    'date': item.get('date'),
                    'netflow': item.get('netflow', 0),
                    'source': 'CRYPTOQUANT'
                })
            
            logger.info(f"获取CryptoQuant净流入数据{len(results)}条")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CryptoQuant API调用失败: {e}")
            raise
    
    def close(self):
        self.session.close()
