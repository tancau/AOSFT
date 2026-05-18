"""
定时调度模块
使用APScheduler实现定时任务
"""
from datetime import datetime
from typing import Callable, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging


class TradingScheduler:
    def __init__(self, config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        self.add_cron_job(
            job_func=self._data_collection_job,
            hour=0, minute=5,
            job_id='data_collection',
            name='每日数据采集'
        )
        
        self.add_cron_job(
            job_func=self._trading_job,
            hour=0, minute=10,
            job_id='trading',
            name='每日交易执行'
        )
        
        self.add_cron_job(
            job_func=self._risk_check_job,
            hour='*/4',
            job_id='risk_check',
            name='风控检查(每4小时)'
        )
        
        self.add_cron_job(
            job_func=self._flash_crash_monitor,
            minute='*/15',
            job_id='flash_crash',
            name='闪崩监控(每15分钟)'
        )
        
        self.add_cron_job(
            job_func=self._data_freshness_check,
            hour='*',
            job_id='data_freshness',
            name='数据新鲜度检查(每小时)'
        )
        
        self.add_cron_job(
            job_func=self._monitoring_metrics_update,
            minute='*/5',
            job_id='monitoring',
            name='监控指标更新(每5分钟)'
        )
        
        self.logger.info(f"已注册{len(self.scheduler.get_jobs())}个定时任务")
    
    def add_cron_job(
        self,
        job_func: Callable,
        job_id: str,
        name: str,
        **cron_args
    ):
        trigger = CronTrigger(**cron_args)
        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True
        )
        self.logger.info(f"注册定时任务: {name} [{job_id}]")
    
    def add_interval_job(
        self,
        job_func: Callable,
        job_id: str,
        name: str,
        seconds: int = 60,
        minutes: int = 0,
        hours: int = 0
    ):
        interval = seconds + minutes * 60 + hours * 3600
        self.scheduler.add_job(
            job_func,
            'interval',
            seconds=interval,
            id=job_id,
            name=name,
            replace_existing=True
        )
        self.logger.info(f"注册间隔任务: {name} [{job_id}] 间隔{interval}秒")
    
    def _data_collection_job(self):
        self.logger.info("开始执行数据采集任务")
        try:
            self.logger.info("数据采集任务完成")
        except Exception as e:
            self.logger.error(f"数据采集任务失败: {e}", exc_info=True)
    
    def _trading_job(self):
        self.logger.info("开始执行交易任务")
        try:
            self.logger.info("交易任务完成")
        except Exception as e:
            self.logger.error(f"交易任务失败: {e}", exc_info=True)
    
    def _risk_check_job(self):
        self.logger.debug("执行风控检查")
    
    def _flash_crash_monitor(self):
        self.logger.debug("执行闪崩监控")
    
    def _data_freshness_check(self):
        self.logger.debug("执行数据新鲜度检查")
    
    def _monitoring_metrics_update(self):
        self.logger.debug("更新监控指标")
    
    def start(self):
        self.logger.info("启动定时调度器...")
        self.scheduler.start()
        self.logger.info("定时调度器已启动，按Ctrl+C停止")
        
        try:
            while self.scheduler.running:
                import time
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
    
    def stop(self):
        self.logger.info("停止定时调度器...")
        self.scheduler.shutdown(wait=True)
        self.logger.info("定时调度器已停止")
    
    def get_jobs(self):
        return self.scheduler.get_jobs()
    
    def pause_job(self, job_id: str):
        self.scheduler.pause_job(job_id)
        self.logger.info(f"暂停任务: {job_id}")
    
    def resume_job(self, job_id: str):
        self.scheduler.resume_job(job_id)
        self.logger.info(f"恢复任务: {job_id}")
