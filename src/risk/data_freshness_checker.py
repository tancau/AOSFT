"""
数据新鲜度检查器
检查所有依赖数据的新鲜度
"""
import logging
from datetime import datetime
from typing import List
from ..models.repository import DataRepository
from ..models.data_timestamp_manager import DataTimestampManager
from ..models.enums import DataSource

logger = logging.getLogger("aosft")


class DataFreshnessChecker:
    def __init__(self, repo: DataRepository, stale_threshold: int = 3):
        self.repo = repo
        self.timestamp_manager = DataTimestampManager(repo.db_path)
        self.stale_threshold = stale_threshold
    
    def check_data_freshness(self) -> dict:
        last_updates = self.timestamp_manager.get_all_last_update_times()
        now = datetime.now()
        results = {}
        all_fresh = True
        
        for source_name, info in last_updates.items():
            last_update = datetime.fromisoformat(info['last_update'])
            hours_since_update = (now - last_update).total_seconds() / 3600
            latest_date = info['latest_data_date']
            delay_days = (now - datetime.strptime(latest_date, "%Y-%m-%d")).days
            
            is_fresh = delay_days < self.stale_threshold
            if not is_fresh:
                all_fresh = False
            
            results[source_name] = {
                'last_update': info['last_update'],
                'latest_data_date': latest_date,
                'hours_since_update': round(hours_since_update, 1),
                'delay_days': delay_days,
                'is_fresh': is_fresh
            }
        
        results['all_fresh'] = all_fresh
        return results
    
    def get_stale_data_sources(self) -> List[str]:
        freshness = self.check_data_freshness()
        stale = []
        for source_name, info in freshness.items():
            if source_name == 'all_fresh':
                continue
            if not info.get('is_fresh', True):
                stale.append(source_name)
        return stale
    
    def is_critical_data_fresh(self) -> tuple[bool, str]:
        freshness = self.check_data_freshness()
        
        if freshness.get('all_fresh', True):
            return True, "所有数据新鲜度正常"
        
        stale_sources = self.get_stale_data_sources()
        msg = f"数据过期: {', '.join(stale_sources)}"
        logger.warning(f"[DATA-FRESHNESS] {msg}")
        return False, msg
    
    def check_and_alert(self) -> dict:
        freshness = self.check_data_freshness()
        stale_sources = self.get_stale_data_sources()
        
        if stale_sources:
            logger.warning(
                f"[DATA-FRESHNESS-ALERT] {len(stale_sources)}个数据源过期: "
                f"{', '.join(stale_sources)}"
            )
        
        return {
            'freshness': freshness,
            'stale_sources': stale_sources,
            'needs_alert': len(stale_sources) > 0
        }
