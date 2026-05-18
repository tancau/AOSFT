#!/usr/bin/env python3
"""
AOSFT-MVP主程序入口
链上与体制感知的BTC趋势跟踪系统
"""
import sys
import signal
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import setup_logger, get_audit_logger
from src.models.repository import DataRepository
from src.collectors.coordinator import DataCollectionCoordinator
from src.strategy.engine import StrategyEngine
from src.execution.gateway import ExecutionGateway
from src.risk.controller import RiskController
from src.risk.risk_interceptor import RiskInterceptor
from src.collectors.okx_interface import OKXMarketInterface, OKXTradingInterface
from src.collectors.data_source_interface import TelegramNotifier
from src.monitor.monitor import Monitor
from src.scheduler.scheduler import TradingScheduler


class AOSFTApp:
    def __init__(self):
        self.config = None
        self.logger = None
        self.audit = None
        self.repo = None
        self.coordinator = None
        self.strategy = None
        self.execution = None
        self.risk = None
        self.interceptor = None
        self.monitor = None
        self.notifier = None
        self.scheduler = None
        self._running = False
    
    def initialize(self):
        self.config = Config.load()
        self.logger = setup_logger(self.config.log_level, self.config.log_dir)
        self.audit = get_audit_logger(self.config.log_level, self.config.log_dir)
        
        self.logger.info("=" * 60)
        self.logger.info("AOSFT-MVP系统初始化")
        self.logger.info("交易所: OKX")
        self.logger.info(f"数据库: {self.config.database_path}")
        self.logger.info(f"策略参数: MA={self.config.strategy.ma_period} "
                         f"ATR={self.config.strategy.atr_period} "
                         f"止损倍数={self.config.strategy.stop_atr_multiplier}")
        
        missing = self.config.validate_required_configs()
        if missing:
            self.logger.warning(f"缺失配置项: {', '.join(missing)}")
            self.logger.warning("部分功能可能不可用，请检查.env文件")
        
        self.repo = DataRepository(self.config.database_path)
        
        self.coordinator = DataCollectionCoordinator(self.repo, self.config)
        
        self.strategy = StrategyEngine(self.repo, self.config)
        
        self.notifier = None
        if self.config.api.telegram_bot_token and self.config.api.telegram_chat_id:
            self.notifier = TelegramNotifier(
                self.config.api.telegram_bot_token,
                self.config.api.telegram_chat_id
            )
        
        self.monitor = Monitor(self.repo, self.notifier)
        
        market_interface = OKXMarketInterface(
            api_key=self.config.api.okx_api_key,
            secret=self.config.api.okx_secret,
            password=self.config.api.okx_password
        )
        
        trading_interface = OKXTradingInterface(
            api_key=self.config.api.okx_api_key,
            secret=self.config.api.okx_secret,
            password=self.config.api.okx_password,
            slippage_tolerance=self.config.order.slippage_tolerance
        )
        
        self.execution = ExecutionGateway(
            self.repo, trading_interface,
            limit_order_timeout=self.config.order.limit_order_timeout,
            max_order_timeout=self.config.order.max_order_timeout
        )
        
        self.risk = RiskController(self.repo, self.config, market_interface)
        self.interceptor = RiskInterceptor(self.repo)
        
        self._setup_signal_handlers()
        
        self.logger.info("AOSFT-MVP系统初始化完成")
        self.logger.info("=" * 60)
    
    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        self.logger.info(f"收到信号{signum}，正在关闭...")
        self._running = False
    
    def run_daily_cycle(self):
        self.logger.info("=" * 40)
        self.logger.info(f"开始每日交易周期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        self.logger.info("[1/6] 数据采集...")
        try:
            collection_result = self.coordinator.collect_all()
            self.audit.log_data_collection(
                source="ALL", status="SUCCESS",
                records=sum(v for v in collection_result.values() if isinstance(v, int))
            )
        except Exception as e:
            self.logger.error(f"数据采集失败: {e}")
            self.audit.log_data_collection(source="ALL", status="FAILED", records=0, error=str(e))
            return
        
        self.logger.info("[2/6] 风控前置检查...")
        if not self.interceptor.quick_check():
            self.logger.info("风控前置检查未通过，今日不交易")
            return
        
        self.logger.info("[3/6] 策略决策...")
        try:
            signal = self.strategy.run_daily()
        except Exception as e:
            self.logger.error(f"策略计算失败: {e}")
            return
        
        if signal is None:
            self.logger.info("今日无交易信号")
        else:
            self.logger.info(f"生成信号: {signal.signal_type.value} reason={signal.reason}")
            
            position = self.repo.load_current_position()
            
            if signal.signal_type.is_close_signal and position:
                self.logger.info("[4/6] 执行平仓...")
                result = self.execution.execute_close(signal, position['amount'])
                if result:
                    self.repo.update_position(
                        position['id'],
                        status='CLOSED',
                        exit_price=result.get('avg_price', signal.price),
                        exit_time=datetime.now().isoformat(),
                        exit_reason=signal.reason
                    )
                    if self.notifier:
                        self.notifier.notify_trade(
                            'SELL', signal.symbol, position['amount'],
                            signal.price, reason=signal.reason
                        )
            
            elif signal.signal_type.value == 'OPEN' and not position:
                equity = self.repo.get_latest_equity()
                if equity and equity['equity'] > 0:
                    from src.indicators.calculator import TechnicalIndicators
                    import pandas as pd
                    ohlcv_data = self.repo.load_ohlcv(limit=50)
                    if ohlcv_data:
                        df = pd.DataFrame(ohlcv_data)
                        tech = TechnicalIndicators()
                        df = tech.calculate_all(df, self.config.strategy.ma_period,
                                                self.config.strategy.atr_period,
                                                self.config.strategy.atr_ma_period)
                        atr = df.iloc[-1]['atr']
                        
                        amount, stop_price = self.strategy.position_manager.calculate_position_size(
                            equity['equity'], signal.price, atr
                        )
                        
                        self.logger.info(f"[4/6] 执行开仓: amount={amount:.8f} stop={stop_price:.2f}")
                        result = self.execution.execute_open(signal, amount)
                        
                        if result:
                            from src.models.schemas import Position
                            from src.models.enums import PositionStatus
                            pos = Position(
                                symbol=signal.symbol,
                                entry_price=signal.price,
                                amount=amount,
                                stop_price=stop_price,
                                status=PositionStatus.OPEN,
                                entry_time=datetime.now().isoformat()
                            )
                            self.repo.save_position(pos)
                            
                            if self.notifier:
                                self.notifier.notify_trade(
                                    'BUY', signal.symbol, amount,
                                    signal.price, reason=signal.reason
                                )
        
        self.logger.info("[5/6] 风控检查...")
        risk_actions = self.risk.run_risk_check()
        for action_type, risk_signal in risk_actions:
            self.logger.warning(f"风控触发: {action_type} {risk_signal.reason}")
            if self.notifier:
                self.notifier.notify_alert(action_type, risk_signal.reason, "WARNING")
        
        self.logger.info("[6/6] 更新监控指标...")
        self.monitor.update_data_freshness_metrics()
        self.monitor.update_strategy_performance_metrics()
        self.monitor.update_risk_stats_metrics()
        
        self.logger.info(f"每日交易周期完成: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.logger.info("=" * 40)
    
    def run(self):
        self.initialize()
        self._running = True
        
        try:
            self.scheduler = TradingScheduler(self.config, self.logger)
            
            self.scheduler._data_collection_job = self._wrapped_data_collection
            self.scheduler._trading_job = self._wrapped_trading
            self.scheduler._risk_check_job = self._wrapped_risk_check
            
            self.scheduler.start()
        except KeyboardInterrupt:
            self.logger.info("系统收到中断信号")
        except Exception as e:
            self.logger.error(f"系统异常退出: {e}", exc_info=True)
            sys.exit(1)
        finally:
            self.shutdown()
    
    def _wrapped_data_collection(self):
        if not self._running:
            return
        try:
            self.coordinator.collect_all()
        except Exception as e:
            self.logger.error(f"数据采集任务失败: {e}")
    
    def _wrapped_trading(self):
        if not self._running:
            return
        try:
            self.run_daily_cycle()
        except Exception as e:
            self.logger.error(f"交易任务失败: {e}")
    
    def _wrapped_risk_check(self):
        if not self._running:
            return
        try:
            risk_actions = self.risk.run_risk_check()
            for action_type, signal in risk_actions:
                self.logger.warning(f"风控触发: {action_type}")
                if self.notifier:
                    self.notifier.notify_alert(action_type, signal.reason)
        except Exception as e:
            self.logger.error(f"风控检查失败: {e}")
    
    def shutdown(self):
        self._running = False
        self.logger.info("关闭AOSFT-MVP系统...")
        
        if self.coordinator:
            self.coordinator.close()
        if self.scheduler:
            self.scheduler.stop()
        
        self.logger.info("AOSFT-MVP系统已停止")


def main():
    app = AOSFTApp()
    app.run()


if __name__ == "__main__":
    main()
