#!/usr/bin/env python3
"""
AOSFT-MVP主程序入口
链上与体制感知的BTC趋势跟踪系统
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.scheduler.scheduler import TradingScheduler


def main():
    config = Config.load()
    logger = setup_logger(config.log_level, config.log_dir)
    logger.info("=" * 60)
    logger.info("AOSFT-MVP系统启动")
    logger.info("交易所: OKX")
    logger.info(f"数据库: {config.database_path}")
    logger.info("=" * 60)
    
    try:
        scheduler = TradingScheduler(config, logger)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("系统收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"系统异常退出: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("AOSFT-MVP系统已停止")


if __name__ == "__main__":
    main()
