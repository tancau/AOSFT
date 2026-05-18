"""
OKX交易所接口封装
封装行情数据查询和交易执行接口
"""
import time
import logging
from typing import Optional, List
from datetime import datetime
import ccxt
import pandas as pd

logger = logging.getLogger("aosft")


class OKXMarketInterface:
    def __init__(self, api_key: str, secret: str, password: str, testnet: bool = False):
        self.exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        if testnet:
            self.exchange.set_sandbox_mode(True)
        
        self.max_retries = 3
        self.retry_delay = 1
    
    def _retry_call(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except ccxt.NetworkError as e:
                logger.warning(f"网络错误(尝试{attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            except ccxt.ExchangeError as e:
                logger.error(f"交易所错误: {e}")
                raise
        raise ccxt.NetworkError(f"重试{self.max_retries}次后仍失败")
    
    def fetch_ohlcv(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        limit: int = 100,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        raw = self._retry_call(
            self.exchange.fetch_ohlcv,
            symbol, timeframe, since, limit
        )
        
        df = pd.DataFrame(raw, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df = df.drop(columns=['timestamp'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        logger.info(f"获取{symbol}日线数据{len(df)}条")
        return df
    
    def fetch_ticker(self, symbol: str = "BTC/USDT") -> dict:
        ticker = self._retry_call(self.exchange.fetch_ticker, symbol)
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'last': ticker.get('last'),
            'bid': ticker.get('bid'),
            'ask': ticker.get('ask'),
            'high': ticker.get('high'),
            'low': ticker.get('low'),
            'volume': ticker.get('baseVolume'),
        }
        
        logger.debug(f"获取{symbol}最新价格: {result['last']}")
        return result
    
    def close(self):
        self.exchange.close()


class OKXTradingInterface:
    def __init__(
        self,
        api_key: str,
        secret: str,
        password: str,
        testnet: bool = False,
        slippage_tolerance: float = 0.002
    ):
        self.exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        if testnet:
            self.exchange.set_sandbox_mode(True)
        
        self.slippage_tolerance = slippage_tolerance
        self.max_retries = 3
        self.retry_delay = 1
    
    def _retry_call(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except ccxt.NetworkError as e:
                logger.warning(f"网络错误(尝试{attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            except ccxt.ExchangeError as e:
                logger.error(f"交易所错误: {e}")
                raise
        raise ccxt.NetworkError(f"重试{self.max_retries}次后仍失败")
    
    def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> dict:
        order = self._retry_call(
            self.exchange.create_limit_order,
            symbol, side, amount, price
        )
        
        logger.info(
            f"创建限价单: {side} {amount} {symbol} @ {price}, "
            f"order_id={order['id']}"
        )
        return self._format_order(order)
    
    def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float
    ) -> dict:
        order = self._retry_call(
            self.exchange.create_market_order,
            symbol, side, amount
        )
        
        logger.info(
            f"创建市价单: {side} {amount} {symbol}, "
            f"order_id={order['id']}"
        )
        return self._format_order(order)
    
    def cancel_order(self, order_id: str, symbol: str = "BTC/USDT") -> dict:
        result = self._retry_call(
            self.exchange.cancel_order,
            order_id, symbol
        )
        logger.info(f"撤销订单: order_id={order_id}")
        return result
    
    def fetch_order(self, order_id: str, symbol: str = "BTC/USDT") -> dict:
        order = self._retry_call(
            self.exchange.fetch_order,
            order_id, symbol
        )
        return self._format_order(order)
    
    def fetch_balance(self) -> dict:
        balance = self._retry_call(self.exchange.fetch_balance)
        
        usdt = balance.get('USDT', {})
        result = {
            'total': usdt.get('total', 0),
            'free': usdt.get('free', 0),
            'used': usdt.get('used', 0),
        }
        
        logger.debug(f"查询余额: USDT total={result['total']}")
        return result
    
    def fetch_positions(self, symbol: str = "BTC/USDT") -> List[dict]:
        try:
            self.exchange.options['defaultType'] = 'swap'
            positions = self._retry_call(self.exchange.fetch_positions, [symbol])
            return positions
        finally:
            self.exchange.options['defaultType'] = 'spot'
    
    def fetch_funding_rate(self, symbol: str = "BTC/USDT:USDT") -> Optional[float]:
        try:
            self.exchange.options['defaultType'] = 'swap'
            funding = self._retry_call(self.exchange.fetch_funding_rate, symbol)
            return funding.get('fundingRate')
        except Exception as e:
            logger.warning(f"获取资金费率失败: {e}")
            return None
        finally:
            self.exchange.options['defaultType'] = 'spot'
    
    def _format_order(self, order: dict) -> dict:
        return {
            'id': order.get('id'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'type': order.get('type'),
            'amount': order.get('amount'),
            'price': order.get('price'),
            'status': order.get('status'),
            'filled': order.get('filled', 0),
            'cost': order.get('cost', 0),
            'fee': order.get('fee', {}).get('cost', 0),
            'timestamp': order.get('timestamp'),
        }
    
    def close(self):
        self.exchange.close()
