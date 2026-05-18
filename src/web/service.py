"""
AOSFT-MVP Web UI 数据服务
为Streamlit前端提供数据
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import numpy as np


class DashboardService:
    def __init__(self, db_path: str = "data/paper_trading.db"):
        self.db_path = db_path
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_latest_price(self) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM daily_ohlcv 
                ORDER BY date DESC LIMIT 1
            """).fetchone()
            return dict(row) if row else None
    
    def get_price_history(self, days: int = 90) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT date, open, high, low, close, volume 
                FROM daily_ohlcv 
                ORDER BY date ASC
                LIMIT ?
            """, conn, params=(days,))
        return df
    
    def get_current_position(self) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM positions WHERE status = 'OPEN'
                ORDER BY entry_time DESC LIMIT 1
            """).fetchone()
            return dict(row) if row else None
    
    def get_equity_history(self) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query(
                "SELECT * FROM account_equity ORDER BY date ASC",
                conn
            )
        return df
    
    def get_latest_equity(self) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM account_equity 
                ORDER BY date DESC LIMIT 1
            """).fetchone()
            return dict(row) if row else None
    
    def get_trade_signals(self, limit: int = 50) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM trade_signals 
                ORDER BY timestamp DESC LIMIT ?
            """, conn, params=(limit,))
        return df
    
    def get_fear_greed_history(self, days: int = 30) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM fear_greed_index 
                ORDER BY date ASC LIMIT ?
            """, conn, params=(days,))
        return df
    
    def get_netflow_history(self, days: int = 30) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM onchain_netflow 
                ORDER BY date ASC LIMIT ?
            """, conn, params=(days,))
        return df
    
    def get_risk_interceptions(self, limit: int = 20) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM risk_interceptions 
                ORDER BY timestamp DESC LIMIT ?
            """, conn, params=(limit,))
        return df
    
    def get_circuit_breaker_events(self) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query(
                "SELECT * FROM circuit_breaker_events ORDER BY trigger_time DESC",
                conn
            )
        return df
    
    def get_system_config(self) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query(
                "SELECT * FROM system_config ORDER BY key",
                conn
            )
        return df
    
    def get_closed_positions(self) -> pd.DataFrame:
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM positions WHERE status = 'CLOSED'
                ORDER BY exit_time DESC
            """, conn)
        return df
    
    def get_monitoring_metrics(self, metric_type: str = None) -> pd.DataFrame:
        with self._get_conn() as conn:
            if metric_type:
                df = pd.read_sql_query("""
                    SELECT * FROM monitoring_metrics 
                    WHERE metric_type = ?
                    ORDER BY timestamp DESC LIMIT 100
                """, conn, params=(metric_type,))
            else:
                df = pd.read_sql_query("""
                    SELECT * FROM monitoring_metrics 
                    ORDER BY timestamp DESC LIMIT 100
                """, conn)
        return df
    
    def get_summary(self) -> dict:
        latest_price = self.get_latest_price()
        latest_equity = self.get_latest_equity()
        position = self.get_current_position()
        
        price = float(latest_price['close']) if latest_price else 0
        
        if latest_equity:
            equity = float(latest_equity['equity'])
            cash = float(latest_equity['cash'])
            drawdown = float(latest_equity['drawdown'])
        else:
            equity, cash, drawdown = 10000, 10000, 0
        
        position_value = equity - cash
        pnl = equity - 10000
        
        with self._get_conn() as conn:
            signal_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM trade_signals"
            ).fetchone()['cnt']
            closed_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM positions WHERE status='CLOSED'"
            ).fetchone()['cnt']
            interception_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM risk_interceptions"
            ).fetchone()['cnt']
        
        return {
            'btc_price': price,
            'equity': equity,
            'cash': cash,
            'position_value': position_value,
            'pnl': pnl,
            'pnl_pct': pnl / 10000 * 100 if 10000 > 0 else 0,
            'drawdown': drawdown,
            'has_position': position is not None,
            'signal_count': signal_count,
            'closed_trades': closed_count,
            'interception_count': interception_count,
        }
