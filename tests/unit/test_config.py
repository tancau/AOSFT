"""
配置管理单元测试
"""
import pytest
import os
from src.utils.config import Config, mask_api_key, StrategyConfig


class TestMaskApiKey:
    def test_mask_normal_key(self):
        assert mask_api_key("abcdefghijklmnop") == "abcdefgh***"
    
    def test_mask_short_key(self):
        assert mask_api_key("abc") == "***"
    
    def test_mask_empty_key(self):
        assert mask_api_key("") == "***"
    
    def test_mask_exact_length(self):
        result = mask_api_key("12345678")
        assert "***" in result


class TestStrategyConfig:
    def test_default_values(self):
        config = StrategyConfig()
        assert config.ma_period == 20
        assert config.atr_period == 14
        assert config.position_ratio == 0.5
    
    def test_invalid_position_ratio(self):
        with pytest.raises(ValueError):
            StrategyConfig(position_ratio=1.5)
    
    def test_invalid_max_loss(self):
        with pytest.raises(ValueError):
            StrategyConfig(max_loss_per_trade=0)
    
    def test_boundary_values(self):
        config = StrategyConfig(position_ratio=1.0, max_loss_per_trade=1.0)
        assert config.position_ratio == 1.0
