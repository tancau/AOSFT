"""
数据质量评分器
根据数据延迟天数计算质量评分
"""
import logging
from datetime import datetime
from typing import Optional
from .data_timestamp_manager import DataTimestampManager
from .enums import DataSource


logger = logging.getLogger("aosft")


class DataQualityScorer:
    def __init__(
        self,
        timestamp_manager: DataTimestampManager,
        full_threshold: int = 1,
        downgrade_threshold: int = 2,
        stale_threshold: int = 3
    ):
        self.timestamp_manager = timestamp_manager
        self.full_threshold = full_threshold
        self.downgrade_threshold = downgrade_threshold
        self.stale_threshold = stale_threshold
    
    def calculate_score(self, delay_days: int) -> float:
        if delay_days <= self.full_threshold:
            return 1.0
        elif delay_days <= self.downgrade_threshold:
            return 0.8
        elif delay_days < self.stale_threshold:
            return 0.5
        else:
            logger.warning(
                f"[DATA-QUALITY] 数据延迟{delay_days}天>=阈值{self.stale_threshold}天，"
                f"评分0.3，建议暂停交易"
            )
            return 0.3
    
    def mark_quality_score(
        self,
        source: DataSource,
        data_date: str
    ) -> float:
        delay_days = self.timestamp_manager.calculate_freshness(source, data_date)
        score = self.calculate_score(delay_days)
        
        logger.debug(
            f"[DATA-QUALITY] source={source.value} date={data_date} "
            f"delay={delay_days}days score={score}"
        )
        
        return score
    
    def get_quality_score(
        self,
        source: DataSource,
        data_date: str
    ) -> float:
        delay_days = self.timestamp_manager.get_freshness_for_date(source, data_date)
        return self.calculate_score(delay_days)
    
    def is_data_usable(self, source: DataSource, data_date: str) -> bool:
        delay_days = self.timestamp_manager.calculate_freshness(source, data_date)
        return delay_days < self.stale_threshold
    
    def check_all_sources(
        self,
        sources: list[tuple[DataSource, str]]
    ) -> dict:
        results = {}
        all_usable = True
        
        for source, data_date in sources:
            delay_days = self.timestamp_manager.calculate_freshness(source, data_date)
            score = self.calculate_score(delay_days)
            usable = delay_days < self.stale_threshold
            
            results[source.value] = {
                'data_date': data_date,
                'delay_days': delay_days,
                'quality_score': score,
                'is_usable': usable
            }
            
            if not usable:
                all_usable = False
        
        results['all_usable'] = all_usable
        return results
