"""
数据时间戳管理器
标记数据采集时间、计算数据新鲜度
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from .enums import DataSource


class DataTimestampManager:
    def __init__(self, db_path: str = "data/aosft.db"):
        self.db_path = db_path
    
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def mark_collection_time(
        self,
        source: DataSource,
        data_date: str,
        collected_at: Optional[str] = None
    ) -> int:
        if collected_at is None:
            collected_at = datetime.now().isoformat()
        
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_timestamps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    data_date TEXT NOT NULL,
                    collected_at TEXT NOT NULL,
                    freshness_days INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(source, data_date)
                )
            """)
            
            now = datetime.now()
            data_dt = datetime.strptime(data_date, "%Y-%m-%d")
            freshness_days = (now - data_dt).days
            
            cursor = conn.execute("""
                INSERT OR REPLACE INTO data_timestamps 
                (source, data_date, collected_at, freshness_days, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (source.value, data_date, collected_at, freshness_days, now.isoformat()))
            
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def calculate_freshness(self, source: DataSource, data_date: str) -> int:
        now = datetime.now()
        data_dt = datetime.strptime(data_date, "%Y-%m-%d")
        return (now - data_dt).days
    
    def get_last_update_time(self, source: DataSource) -> Optional[str]:
        conn = self._get_conn()
        try:
            row = conn.execute("""
                SELECT collected_at FROM data_timestamps
                WHERE source = ?
                ORDER BY collected_at DESC LIMIT 1
            """, (source.value,)).fetchone()
            return row['collected_at'] if row else None
        finally:
            conn.close()
    
    def get_all_last_update_times(self) -> dict:
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT source, MAX(collected_at) as last_update, MAX(data_date) as latest_data_date
                FROM data_timestamps
                GROUP BY source
            """).fetchall()
            return {
                row['source']: {
                    'last_update': row['last_update'],
                    'latest_data_date': row['latest_data_date']
                }
                for row in rows
            }
        finally:
            conn.close()
    
    def get_freshness_for_date(self, source: DataSource, data_date: str) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute("""
                SELECT freshness_days FROM data_timestamps
                WHERE source = ? AND data_date = ?
            """, (source.value, data_date)).fetchone()
            return row['freshness_days'] if row else self.calculate_freshness(source, data_date)
        finally:
            conn.close()
