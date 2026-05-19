"""
链上数据接口封装
获取交易所BTC净流入等链上数据
"""
import logging
import requests
from typing import Optional, List
from datetime import datetime, timedelta
from ..utils.rate_limiter import create_rate_limited_client, RateLimitedAPIClient

logger = logging.getLogger("aosft")


class GlassnodeInterface:
    BASE_URL = "https://api.glassnode.com/v1"

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        session = requests.Session()
        self._client = create_rate_limited_client(
            name="glassnode",
            rate=1.0,
            capacity=3,
            max_retries=3,
            base_delay=1.0,
            session=session
        )

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

            resp = self._client.get(
                f"{self.BASE_URL}/metrics/transactions/transfers_volume_exchanges_net",
                params=params,
                timeout=self.timeout
            )

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
        self._client.session.close()


class CryptoQuantInterface:
    BASE_URL = "https://api.cryptoquant.com/v1"

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {api_key}'})
        self._client = create_rate_limited_client(
            name="cryptoquant",
            rate=1.0,
            capacity=3,
            max_retries=3,
            base_delay=1.0,
            session=session
        )

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

            resp = self._client.get(
                f"{self.BASE_URL}/btc/exchange-flows/net-flow",
                params=params,
                timeout=self.timeout
            )

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
        self._client.session.close()


class CoinMetricsInterface:
    BASE_URL = "https://community-api.coinmetrics.io/v4"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        session = requests.Session()
        self._client = create_rate_limited_client(
            name="coinmetrics",
            rate=1.0,
            capacity=5,
            max_retries=3,
            base_delay=1.0,
            session=session
        )

    def get_exchange_netflow(
        self,
        asset: str = "btc",
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[dict]:
        if until is None:
            until = datetime.now().strftime("%Y-%m-%d")
        if since is None:
            since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            resp = self._client.get(
                f"{self.BASE_URL}/timeseries/asset-metrics",
                params={
                    'assets': asset,
                    'metrics': 'FlowInExNtv,FlowOutExNtv',
                    'frequency': '1d',
                    'start_time': since,
                    'end_time': until,
                },
                timeout=self.timeout
            )

            entries = resp.json().get('data', [])
            results = []
            for item in entries:
                date = item.get('time', '')[:10]
                flow_in = float(item.get('FlowInExNtv', 0))
                flow_out = float(item.get('FlowOutExNtv', 0))
                netflow = flow_in - flow_out
                results.append({
                    'date': date,
                    'netflow': netflow,
                    'source': 'COINMETRICS'
                })

            results.sort(key=lambda x: x['date'])
            logger.info(f"获取CoinMetrics净流入数据{len(results)}条")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinMetrics API调用失败: {e}")
            raise

    def get_stablecoin_supply(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[dict]:
        if until is None:
            until = datetime.now().strftime("%Y-%m-%d")
        if since is None:
            since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            resp = self._client.get(
                f"{self.BASE_URL}/timeseries/asset-metrics",
                params={
                    'assets': 'usdt,usdc',
                    'metrics': 'CapMrktCurUSD',
                    'frequency': '1d',
                    'start_time': since,
                    'end_time': until,
                },
                timeout=self.timeout
            )

            entries = resp.json().get('data', [])
            date_map = {}
            for item in entries:
                date = item.get('time', '')[:10]
                asset = item.get('asset', '')
                cap = float(item.get('CapMrktCurUSD', 0))

                if date not in date_map:
                    date_map[date] = {'date': date, 'usdt_supply': 0, 'usdc_supply': 0}

                if asset == 'usdt':
                    date_map[date]['usdt_supply'] = cap
                elif asset == 'usdc':
                    date_map[date]['usdc_supply'] = cap

            results = []
            for date in sorted(date_map.keys()):
                entry = date_map[date]
                entry['total_supply'] = entry['usdt_supply'] + entry['usdc_supply']
                results.append(entry)

            logger.info(f"获取CoinMetrics稳定币供应数据{len(results)}条")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinMetrics稳定币API调用失败: {e}")
            raise

    def close(self):
        self._client.session.close()
