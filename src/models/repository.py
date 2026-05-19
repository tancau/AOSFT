"""
数据仓库层
封装SQLite数据库CRUD操作
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager
from .schemas import (
    OHLCV, OnchainNetflow, StablecoinSupply, FearGreedIndex,
    TradeSignal, Position, AccountEquity, Order, RiskInterception,
    CircuitBreakerEvent
)
from .enums import (
    MarketRegime, SignalType, PositionStatus, OrderStatus,
    OrderSide, OrderType, DataSource, CircuitBreakerType, InterceptionType
)
from .data_timestamp_manager import DataTimestampManager
from .data_quality_scorer import DataQualityScorer


class DataRepository:
    def __init__(self, db_path: str = "data/aosft.db"):
        self.db_path = db_path
        self.timestamp_manager = DataTimestampManager(db_path)
        self.quality_scorer = DataQualityScorer(self.timestamp_manager)
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ========== OHLCV ==========
    
    def save_ohlcv(self, data: OHLCV) -> int:
        self.timestamp_manager.mark_collection_time(
            DataSource.OKX, data.date, data.collected_at
        )
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO daily_ohlcv
                (symbol, date, open, high, low, close, volume, collected_at, data_quality)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.symbol, data.date, data.open, data.high, data.low,
                  data.close, data.volume, data.collected_at, data.data_quality))
            return cursor.lastrowid
    
    def load_ohlcv(
        self,
        symbol: str = "BTC/USDT",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[dict]:
        with self._get_conn() as conn:
            query = "SELECT * FROM daily_ohlcv WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            if limit:
                query = f"SELECT * FROM ({query} ORDER BY date DESC LIMIT {limit}) ORDER BY date ASC"
            else:
                query += " ORDER BY date ASC"
            
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
    
    def get_latest_ohlcv(self, symbol: str = "BTC/USDT") -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM daily_ohlcv WHERE symbol = ?
                ORDER BY date DESC LIMIT 1
            """, (symbol,)).fetchone()
            return dict(row) if row else None
    
    # ========== Onchain Netflow ==========
    
    def save_netflow(self, data: OnchainNetflow) -> int:
        self.timestamp_manager.mark_collection_time(
            DataSource(data.source.value), data.date, data.collected_at
        )
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO onchain_netflow
                (date, netflow, source, collected_at, data_freshness, data_quality)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data.date, data.netflow, data.source.value,
                  data.collected_at, data.data_freshness, data.data_quality))
            return cursor.lastrowid
    
    def load_netflow(self, days: int = 30) -> List[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM onchain_netflow
                ORDER BY date DESC LIMIT ?
            """, (days,)).fetchall()
            return [dict(r) for r in rows]
    
    # ========== Stablecoin Supply ==========
    
    def save_stablecoin_supply(self, data: StablecoinSupply) -> int:
        self.timestamp_manager.mark_collection_time(
            DataSource.COINGECKO, data.date, data.collected_at
        )
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO stablecoin_supply
                (date, usdt_supply, usdc_supply, total_supply, change_7d, collected_at, data_quality)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data.date, data.usdt_supply, data.usdc_supply,
                  data.total_supply, data.change_7d, data.collected_at, data.data_quality))
            return cursor.lastrowid
    
    def load_stablecoin_supply(self, days: int = 30) -> List[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM stablecoin_supply
                ORDER BY date DESC LIMIT ?
            """, (days,)).fetchall()
            return [dict(r) for r in rows]
    
    # ========== Fear & Greed Index ==========
    
    def save_fear_greed_index(self, data: FearGreedIndex) -> int:
        self.timestamp_manager.mark_collection_time(
            DataSource.ALTERNATIVE_ME, data.date, data.collected_at
        )
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO fear_greed_index
                (date, value, classification, collected_at)
                VALUES (?, ?, ?, ?)
            """, (data.date, data.value, data.classification, data.collected_at))
            return cursor.lastrowid
    
    def load_fear_greed_index(self, days: int = 30) -> List[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM fear_greed_index
                ORDER BY date DESC LIMIT ?
            """, (days,)).fetchall()
            return [dict(r) for r in rows]
    
    # ========== Trade Signals ==========
    
    def save_signal(self, data: TradeSignal) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO trade_signals
                (timestamp, signal_type, symbol, price, regime,
                 netflow_condition, stable_condition, fg_condition, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.timestamp, data.signal_type.value, data.symbol, data.price,
                  data.regime.value, int(data.netflow_condition),
                  int(data.stable_condition), int(data.fg_condition),
                  data.reason, data.created_at))
            return cursor.lastrowid
    
    def load_signals(self, limit: int = 100) -> List[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM trade_signals
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]
    
    # ========== Positions ==========
    
    def save_position(self, data: Position) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO positions
                (symbol, entry_price, amount, stop_price, status,
                 entry_time, exit_price, exit_time, exit_reason, pnl,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.symbol, data.entry_price, data.amount, data.stop_price,
                  data.status.value, data.entry_time, data.exit_price,
                  data.exit_time, data.exit_reason, data.pnl,
                  data.created_at, data.updated_at))
            return cursor.lastrowid
    
    def load_current_position(self) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM positions WHERE status = 'OPEN'
                ORDER BY entry_time DESC LIMIT 1
            """).fetchone()
            return dict(row) if row else None
    
    def update_position(self, position_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        kwargs['updated_at'] = datetime.now().isoformat()
        
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [position_id]
        
        with self._get_conn() as conn:
            conn.execute(f"UPDATE positions SET {set_clause} WHERE id = ?", values)
            return True
    
    # ========== Account Equity ==========
    
    def save_equity(self, data: AccountEquity) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO account_equity
                (date, equity, cash, position_value, daily_pnl, total_pnl,
                 max_equity, drawdown, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.date, data.equity, data.cash, data.position_value,
                  data.daily_pnl, data.total_pnl, data.max_equity,
                  data.drawdown, data.created_at))
            return cursor.lastrowid
    
    def get_latest_equity(self) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM account_equity
                ORDER BY date DESC LIMIT 1
            """).fetchone()
            return dict(row) if row else None
    
    def calculate_max_drawdown(self) -> float:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT MAX(drawdown) as max_dd FROM account_equity
            """).fetchone()
            return row['max_dd'] if row and row['max_dd'] is not None else 0.0
    
    # ========== Orders ==========
    
    def save_order(self, data: Order) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO orders
                (order_id, symbol, side, order_type, amount, price, status,
                 filled_amount, avg_price, fee, created_at, updated_at,
                 timeout_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.order_id, data.symbol, data.side.value, data.order_type.value,
                  data.amount, data.price, data.status.value, data.filled_amount,
                  data.avg_price, data.fee, data.created_at, data.updated_at,
                  data.timeout_at, data.error_message))
            return cursor.lastrowid
    
    def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        filled_amount: float = 0,
        avg_price: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> bool:
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE orders SET status = ?, filled_amount = ?,
                avg_price = ?, error_message = ?, updated_at = ?
                WHERE order_id = ?
            """, (status.value, filled_amount, avg_price, error_message, now, order_id))
            return True
    
    def load_active_orders(self) -> List[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM orders
                WHERE status IN ('pending', 'partial_filled')
                ORDER BY created_at ASC
            """).fetchall()
            return [dict(r) for r in rows]
    
    # ========== Risk Interceptions ==========
    
    def save_interception(self, data: RiskInterception) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO risk_interceptions
                (timestamp, interception_type, signal_type, reason,
                 action_taken, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data.timestamp, data.interception_type.value,
                  data.signal_type.value if data.signal_type else None,
                  data.reason, data.action_taken, data.metadata, data.created_at))
            return cursor.lastrowid
    
    # ========== Circuit Breaker Events ==========
    
    def save_circuit_breaker_event(self, data: CircuitBreakerEvent) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO circuit_breaker_events
                (trigger_time, breaker_type, trigger_value, threshold,
                 recovery_stage, recovery_start_time, recovery_end_time,
                 manual_recovery, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.trigger_time, data.breaker_type.value,
                  data.trigger_value, data.threshold, data.recovery_stage,
                  data.recovery_start_time, data.recovery_end_time,
                  int(data.manual_recovery), data.created_at))
            return cursor.lastrowid
    
    def get_active_circuit_breaker(self) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM circuit_breaker_events
                WHERE recovery_end_time IS NULL OR recovery_end_time > ?
                ORDER BY trigger_time DESC LIMIT 1
            """, (datetime.now().isoformat(),)).fetchone()
            return dict(row) if row else None
    
    # ========== Monitoring Metrics ==========
    
    def save_metric(self, metric_type: str, metric_name: str, value: float,
                    unit: Optional[str] = None, metadata: Optional[dict] = None) -> int:
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO monitoring_metrics
                (metric_type, metric_name, value, unit, timestamp, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (metric_type, metric_name, value, unit, now,
                  json.dumps(metadata) if metadata else None, now))
            return cursor.lastrowid
    
    # ========== System Config ==========
    
    def get_config(self, key: str) -> Optional[str]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM system_config WHERE key = ?", (key,)
            ).fetchone()
            return row['value'] if row else None
    
    def set_config(self, key: str, value: str, description: Optional[str] = None) -> bool:
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO system_config (key, value, description, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value, description, now))
            return True
