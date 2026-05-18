#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有表结构并插入默认配置
"""
import sqlite3
import sys
from pathlib import Path


def create_tables(db_path: str = "data/aosft.db"):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_ohlcv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL CHECK (open > 0),
            high REAL NOT NULL CHECK (high > 0),
            low REAL NOT NULL CHECK (low > 0),
            close REAL NOT NULL CHECK (close > 0),
            volume REAL NOT NULL CHECK (volume >= 0),
            collected_at TEXT NOT NULL,
            data_quality REAL DEFAULT 1.0 CHECK (data_quality >= 0 AND data_quality <= 1.0),
            UNIQUE(symbol, date)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_date ON daily_ohlcv(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_date ON daily_ohlcv(symbol, date)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onchain_netflow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            netflow REAL NOT NULL,
            source TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            data_freshness INTEGER DEFAULT 0,
            data_quality REAL DEFAULT 1.0 CHECK (data_quality >= 0 AND data_quality <= 1.0)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_netflow_date ON onchain_netflow(date)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stablecoin_supply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            usdt_supply REAL NOT NULL CHECK (usdt_supply > 0),
            usdc_supply REAL NOT NULL CHECK (usdc_supply > 0),
            total_supply REAL NOT NULL CHECK (total_supply > 0),
            change_7d REAL,
            collected_at TEXT NOT NULL,
            data_quality REAL DEFAULT 1.0 CHECK (data_quality >= 0 AND data_quality <= 1.0)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stablecoin_date ON stablecoin_supply(date)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fear_greed_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            value INTEGER NOT NULL CHECK (value >= 0 AND value <= 100),
            classification TEXT NOT NULL,
            collected_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fgi_date ON fear_greed_index(date)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL NOT NULL CHECK (price > 0),
            regime TEXT NOT NULL,
            netflow_condition INTEGER NOT NULL,
            stable_condition INTEGER NOT NULL,
            fg_condition INTEGER NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON trade_signals(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_type ON trade_signals(signal_type)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_price REAL NOT NULL CHECK (entry_price > 0),
            amount REAL NOT NULL CHECK (amount > 0),
            stop_price REAL NOT NULL CHECK (stop_price > 0),
            status TEXT NOT NULL CHECK (status IN ('OPEN', 'CLOSED')),
            entry_time TEXT NOT NULL,
            exit_price REAL,
            exit_time TEXT,
            exit_reason TEXT,
            pnl REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_entry_time ON positions(entry_time)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_equity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            equity REAL NOT NULL CHECK (equity >= 0),
            cash REAL NOT NULL CHECK (cash >= 0),
            position_value REAL NOT NULL CHECK (position_value >= 0),
            daily_pnl REAL,
            total_pnl REAL,
            max_equity REAL NOT NULL,
            drawdown REAL NOT NULL CHECK (drawdown >= 0 AND drawdown <= 1),
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equity_date ON account_equity(date)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL UNIQUE,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
            order_type TEXT NOT NULL CHECK (order_type IN ('limit', 'market')),
            amount REAL NOT NULL CHECK (amount > 0),
            price REAL,
            status TEXT NOT NULL CHECK (status IN ('pending', 'partial_filled', 'filled', 'rejected', 'cancelled')),
            filled_amount REAL DEFAULT 0,
            avg_price REAL,
            fee REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            timeout_at TEXT,
            error_message TEXT
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_interceptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            interception_type TEXT NOT NULL,
            signal_type TEXT,
            reason TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interceptions_timestamp ON risk_interceptions(timestamp)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS circuit_breaker_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_time TEXT NOT NULL,
            breaker_type TEXT NOT NULL,
            trigger_value REAL NOT NULL,
            threshold REAL NOT NULL,
            recovery_stage INTEGER DEFAULT 0,
            recovery_start_time TEXT,
            recovery_end_time TEXT,
            manual_recovery INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_breaker_trigger_time ON circuit_breaker_events(trigger_time)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            timestamp TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type_time ON monitoring_metrics(metric_type, timestamp)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    
    default_configs = [
        ('ma_period', '20', '趋势均线周期（日）'),
        ('atr_period', '14', 'ATR计算周期'),
        ('atr_ma_period', '30', 'ATR均值周期'),
        ('netflow_ma_days', '7', '净流入平滑天数'),
        ('stable_change_days', '7', '稳定币变化统计天数'),
        ('netflow_confirm_days', '3', '连续满足平仓信号的天数'),
        ('stable_confirm_days', '3', '稳定币连续天数'),
        ('stop_atr_multiplier', '2.0', '止损ATR倍数'),
        ('position_ratio', '0.5', '仓位占比'),
        ('max_loss_per_trade', '0.05', '单笔最大亏损占比'),
        ('max_drawdown_global', '0.20', '全局最大回撤熔断'),
        ('fear_greed_ceiling', '80', '情绪过热不开仓阈值'),
        ('data_freshness_threshold', '3', '数据新鲜度阈值（天）'),
        ('data_quality_full_threshold', '1', '数据质量满分阈值（天）'),
        ('data_quality_downgrade_threshold', '2', '数据质量降权阈值（天）'),
        ('limit_order_timeout', '300', '限价单超时时间（秒）'),
        ('max_order_timeout', '1800', '订单最大超时时间（秒）'),
        ('recovery_stage1_days', '10', '分级恢复第一阶段天数'),
        ('recovery_stage2_days', '20', '分级恢复第二阶段天数'),
    ]
    
    from datetime import datetime
    now = datetime.now().isoformat()
    
    for key, value, description in default_configs:
        cursor.execute("""
            INSERT OR IGNORE INTO system_config (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
        """, (key, value, description, now))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库初始化完成: {db_path}")
    print(f"✅ 创建表: daily_ohlcv, onchain_netflow, stablecoin_supply, fear_greed_index")
    print(f"✅ 创建表: trade_signals, positions, account_equity, orders")
    print(f"✅ 创建表: risk_interceptions, circuit_breaker_events, monitoring_metrics")
    print(f"✅ 创建表: system_config (含{len(default_configs)}条默认配置)")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/aosft.db"
    create_tables(db_path)
