"""
日志系统模块
配置日志轮转、安全格式化和审计日志
"""
import logging
import re
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


SENSITIVE_PATTERNS = [
    re.compile(r'(api[_-]?key)["\s:=]+["\']?([a-zA-Z0-9_-]{8,})["\']?', re.IGNORECASE),
    re.compile(r'(secret)["\s:=]+["\']?([a-zA-Z0-9_-]{8,})["\']?', re.IGNORECASE),
    re.compile(r'(password)["\s:=]+["\']?([a-zA-Z0-9_-]{8,})["\']?', re.IGNORECASE),
    re.compile(r'(token)["\s:=]+["\']?([a-zA-Z0-9_-]{8,})["\']?', re.IGNORECASE),
]


class SecureFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        for pattern in SENSITIVE_PATTERNS:
            message = pattern.sub(r'\1=***', message)
        return message


class AuditLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_trade(self, action: str, symbol: str, amount: float, price: float, **kwargs):
        self.logger.info(
            f"[AUDIT-TRADE] action={action} symbol={symbol} "
            f"amount={amount:.8f} price={price:.2f} "
            f"{self._format_kwargs(kwargs)}"
        )
    
    def log_signal(self, signal_type: str, regime: str, reason: str, **kwargs):
        self.logger.info(
            f"[AUDIT-SIGNAL] type={signal_type} regime={regime} "
            f"reason='{reason}' {self._format_kwargs(kwargs)}"
        )
    
    def log_risk(self, event: str, action: str, **kwargs):
        self.logger.warning(
            f"[AUDIT-RISK] event={event} action={action} "
            f"{self._format_kwargs(kwargs)}"
        )
    
    def log_config_change(self, key: str, old_value: str, new_value: str, user: str = "system"):
        self.logger.info(
            f"[AUDIT-CONFIG] key={key} old={old_value} new={new_value} user={user}"
        )
    
    def log_data_collection(self, source: str, status: str, records: int, **kwargs):
        self.logger.info(
            f"[AUDIT-DATA] source={source} status={status} records={records} "
            f"{self._format_kwargs(kwargs)}"
        )
    
    def _format_kwargs(self, kwargs: dict) -> str:
        return ' '.join(f"{k}={v}" for k, v in kwargs.items())


def setup_logger(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_name: str = "aosft"
) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(log_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if logger.handlers:
        return logger
    
    formatter = SecureFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = TimedRotatingFileHandler(
        filename=Path(log_dir) / f"{log_name}.log",
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_audit_logger(log_level: str = "INFO", log_dir: str = "logs") -> AuditLogger:
    logger = setup_logger(log_level, log_dir, "audit")
    return AuditLogger(logger)


def cleanup_old_logs(log_dir: str = "logs", keep_days: int = 90):
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    for log_file in log_path.glob("*.log.*"):
        try:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                log_file.unlink()
        except Exception:
            pass
