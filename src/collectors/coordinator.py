"""
数据采集协调器
统一调度各个数据采集器
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.repository import DataRepository
from ..models.schemas import OHLCV, OnchainNetflow, StablecoinSupply, FearGreedIndex
from ..models.enums import DataSource
from ..models.data_quality_scorer import DataQualityScorer
from ..models.data_timestamp_manager import DataTimestampManager

logger = logging.getLogger("aosft")


class DataCollectionCoordinator:
    def __init__(self, repo: DataRepository, config):
        self.repo = repo
        self.config = config
        self.timestamp_manager = DataTimestampManager(repo.db_path)
        self.quality_scorer = DataQualityScorer(self.timestamp_manager)
        self._okx_market = None
        self._glassnode = None
        self._coingecko = None
        self._fear_greed = None
    
    @property
    def okx_market(self):
        if self._okx_market is None:
            from ..collectors.okx_interface import OKXMarketInterface
            self._okx_market = OKXMarketInterface(
                api_key=self.config.api.okx_api_key,
                secret=self.config.api.okx_secret,
                password=self.config.api.okx_password
            )
        return self._okx_market
    
    @property
    def glassnode(self):
        if self._glassnode is None and self.config.api.glassnode_api_key:
            from ..collectors.onchain_interface import GlassnodeInterface
            self._glassnode = GlassnodeInterface(self.config.api.glassnode_api_key)
        return self._glassnode
    
    @property
    def coingecko(self):
        if self._coingecko is None:
            from ..collectors.data_source_interface import CoinGeckoInterface
            self._coingecko = CoinGeckoInterface()
        return self._coingecko
    
    @property
    def fear_greed(self):
        if self._fear_greed is None:
            from ..collectors.data_source_interface import FearGreedInterface
            self._fear_greed = FearGreedInterface()
        return self._fear_greed
    
    def collect_all(self) -> dict:
        results = {
            'ohlcv': self._collect_ohlcv(),
            'netflow': self._collect_netflow(),
            'stablecoin': self._collect_stablecoin(),
            'fear_greed': self._collect_fear_greed(),
            'timestamp': datetime.now().isoformat()
        }
        
        total = sum(1 for v in results.values() if v is not None and v != 0)
        logger.info(f"[COLLECTOR] 数据采集完成: {total}/4个数据源成功")
        
        return results
    
    def _collect_ohlcv(self) -> int:
        try:
            df = self.okx_market.fetch_ohlcv("BTC/USDT", "1d", limit=30)
            count = 0
            
            for _, row in df.iterrows():
                quality = self.quality_scorer.mark_quality_score(
                    DataSource.OKX, row['date']
                )
                
                ohlcv = OHLCV(
                    symbol="BTC/USDT",
                    date=row['date'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    data_quality=quality
                )
                self.repo.save_ohlcv(ohlcv)
                count += 1
            
            logger.info(f"[COLLECTOR] OHLCV数据采集: {count}条")
            return count
        except Exception as e:
            logger.error(f"[COLLECTOR] OHLCV采集失败: {e}")
            return 0
    
    def _collect_netflow(self) -> int:
        try:
            if not self.glassnode:
                logger.warning("[COLLECTOR] Glassnode未配置，跳过链上数据采集")
                return 0
            
            data = self.glassnode.get_exchange_netflow()
            count = 0
            
            for item in data[-30:]:
                quality = self.quality_scorer.mark_quality_score(
                    DataSource.GLASSNODE, item['date']
                )
                
                netflow = OnchainNetflow(
                    date=item['date'],
                    netflow=item['netflow'],
                    source=DataSource.GLASSNODE,
                    data_quality=quality
                )
                self.repo.save_netflow(netflow)
                count += 1
            
            logger.info(f"[COLLECTOR] 链上数据采集: {count}条")
            return count
        except Exception as e:
            logger.error(f"[COLLECTOR] 链上数据采集失败: {e}")
            return 0
    
    def _collect_stablecoin(self) -> int:
        try:
            data = self.coingecko.get_stablecoin_supply(days=30)
            count = 0
            
            for item in data:
                quality = self.quality_scorer.mark_quality_score(
                    DataSource.COINGECKO, item['date']
                )
                
                supply = StablecoinSupply(
                    date=item['date'],
                    usdt_supply=item['usdt_supply'],
                    usdc_supply=item['usdc_supply'],
                    total_supply=item['total_supply'],
                    data_quality=quality
                )
                self.repo.save_stablecoin_supply(supply)
                count += 1
            
            logger.info(f"[COLLECTOR] 稳定币数据采集: {count}条")
            return count
        except Exception as e:
            logger.error(f"[COLLECTOR] 稳定币数据采集失败: {e}")
            return 0
    
    def _collect_fear_greed(self) -> int:
        try:
            data = self.fear_greed.get_fear_greed_index(limit=30)
            count = 0
            
            for item in data:
                fgi = FearGreedIndex(
                    date=item['date'],
                    value=item['value'],
                    classification=item['classification']
                )
                self.repo.save_fear_greed_index(fgi)
                count += 1
            
            logger.info(f"[COLLECTOR] 情绪指数采集: {count}条")
            return count
        except Exception as e:
            logger.error(f"[COLLECTOR] 情绪指数采集失败: {e}")
            return 0
    
    def close(self):
        if self._okx_market:
            self._okx_market.close()
        if self._glassnode:
            self._glassnode.close()
        if self._coingecko:
            self._coingecko.close()
        if self._fear_greed:
            self._fear_greed.close()
