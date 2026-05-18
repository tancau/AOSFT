"""
pytest全局配置和共享fixture
"""
import pytest
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_dir():
    return project_root


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test_aosft.db")
    from scripts.init_db import create_tables
    create_tables(db_path)
    return db_path


@pytest.fixture
def repo(test_db):
    from src.models.repository import DataRepository
    return DataRepository(test_db)


@pytest.fixture
def sample_ohlcv_df():
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=60, freq='D')
    base = 42000
    prices = [base]
    for _ in range(59):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.02)))
    
    df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0.01, 0.005))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0.01, 0.005))) for p in prices],
        'close': prices,
        'volume': np.random.uniform(500, 2000, 60)
    })
    return df


@pytest.fixture
def sample_netflow_df():
    import pandas as pd
    import numpy as np
    np.random.seed(123)
    
    dates = pd.date_range('2024-01-01', periods=60, freq='D')
    return pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'netflow': np.random.normal(-100, 500, 60)
    })


@pytest.fixture
def sample_stablecoin_df():
    import pandas as pd
    import numpy as np
    np.random.seed(456)
    
    dates = pd.date_range('2024-01-01', periods=60, freq='D')
    base_supply = 110e9
    return pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'total_supply': base_supply + np.cumsum(np.random.normal(1e8, 5e8, 60))
    })


@pytest.fixture
def saved_ohlcv_data(repo, sample_ohlcv_df):
    from src.models.schemas import OHLCV
    from src.models.data_quality_scorer import DataQualityScorer
    from src.models.data_timestamp_manager import DataTimestampManager
    from src.models.enums import DataSource
    
    tm = DataTimestampManager(repo.db_path)
    scorer = DataQualityScorer(tm)
    
    for _, row in sample_ohlcv_df.iterrows():
        quality = scorer.mark_quality_score(DataSource.OKX, row['date'])
        ohlcv = OHLCV(
            symbol="BTC/USDT", date=row['date'],
            open=row['open'], high=row['high'],
            low=row['low'], close=row['close'],
            volume=row['volume'], data_quality=quality
        )
        repo.save_ohlcv(ohlcv)
    
    return sample_ohlcv_df
