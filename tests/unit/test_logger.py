"""
日志系统单元测试
"""
import pytest
import logging
from src.utils.logger import SecureFormatter, AuditLogger, setup_logger


class TestSecureFormatter:
    def test_normal_message(self):
        formatter = SecureFormatter(
            fmt='%(message)s'
        )
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='normal message', args=(), exc_info=None
        )
        result = formatter.format(record)
        assert result == 'normal message'
    
    def test_api_key_masked(self):
        formatter = SecureFormatter(fmt='%(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='api_key=abcdefgh12345678', args=(), exc_info=None
        )
        result = formatter.format(record)
        assert '12345678' not in result
        assert '***' in result
    
    def test_secret_masked(self):
        formatter = SecureFormatter(fmt='%(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='secret=mysecretkey123456', args=(), exc_info=None
        )
        result = formatter.format(record)
        assert 'mysecretkey123456' not in result


class TestAuditLogger:
    def setup_method(self):
        logger = logging.getLogger('test_audit')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        self.audit = AuditLogger(logger)
    
    def test_log_trade(self):
        self.audit.log_trade('BUY', 'BTC/USDT', 0.1, 50000)
    
    def test_log_signal(self):
        self.audit.log_signal('OPEN', 'BULL_VOLATILE', 'All conditions met')
    
    def test_log_risk(self):
        self.audit.log_risk('STOP_LOSS', 'FORCED_CLOSE')
    
    def test_log_config_change(self):
        self.audit.log_config_change('ma_period', '20', '25', 'admin')


class TestSetupLogger:
    def test_setup_returns_logger(self):
        logger = setup_logger('DEBUG', '/tmp/test_aosft_logs')
        assert logger is not None
        assert logger.name == 'aosft'
    
    def test_logger_level(self):
        logger = setup_logger('WARNING', '/tmp/test_aosft_logs')
        assert logger.level == logging.WARNING
