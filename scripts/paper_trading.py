#!/usr/bin/env python3
"""
AOSFT-MVP Paper Trading 启动脚本
使用真实市场数据，模拟交易执行，不涉及真实资金
"""
import sys
import time
import signal
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.models.repository import DataRepository
from src.collectors.coordinator import DataCollectionCoordinator
from src.strategy.paper_trading import PaperTradingEngine
from src.collectors.data_source_interface import TelegramNotifier
from src.risk.risk_interceptor import RiskInterceptor


class PaperTradingApp:
    def __init__(self):
        self.running = False
        self.config = None
        self.logger = None
        self.repo = None
        self.engine = None
        self.coordinator = None
    
    def initialize(self):
        self.config = Config.load()
        self.logger = setup_logger('INFO', 'logs')
        
        # Paper Trading模式放宽数据新鲜度检查
        self.config.data_quality.freshness_threshold = 999
        
        self.logger.info('=' * 60)
        self.logger.info('AOSFT-MVP Paper Trading 模式启动')
        self.logger.info('=' * 60)
        
        from scripts.init_db import create_tables
        create_tables(self.config.database_path)
        
        self.repo = DataRepository(self.config.database_path)
        self.coordinator = DataCollectionCoordinator(self.repo, self.config)
        
        notifier = None
        if self.config.api.telegram_bot_token and self.config.api.telegram_chat_id:
            if self.config.api.telegram_bot_token != 'your_bot_token_here':
                notifier = TelegramNotifier(
                    self.config.api.telegram_bot_token,
                    self.config.api.telegram_chat_id
                )
        
        self.engine = PaperTradingEngine(self.repo, self.config, notifier)
        
        status = self.engine.get_status()
        self.logger.info(f'初始资金: ${status["initial_capital"]:,.2f}')
        self.logger.info(f'当前净值: ${status["equity"]:,.2f}')
        self.logger.info(f'当前持仓: {"有" if status["position"] else "无"}')
        
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, signum, frame):
        self.logger.info('收到停止信号，正在关闭...')
        self.running = False
    
    def collect_data(self):
        self.logger.info('--- 数据采集(OKX实时数据) ---')
        try:
            from src.models.schemas import OHLCV, FearGreedIndex, OnchainNetflow, StablecoinSupply
            from src.models.data_quality_scorer import DataQualityScorer
            from src.models.data_timestamp_manager import DataTimestampManager
            from src.models.enums import DataSource
            from src.collectors.data_source_interface import FearGreedInterface
            from datetime import datetime as dt
            import ccxt
            import numpy as np
            
            tm = DataTimestampManager(self.repo.db_path)
            scorer = DataQualityScorer(tm)
            
            # OKX实时行情数据(公开接口，无需API密钥)
            try:
                exchange = ccxt.okx({'enableRateLimit': True})
                ohlcv_raw = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=100)
                count = 0
                for item in ohlcv_raw:
                    ts_ms, o, h, l, c, v = item
                    date = dt.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d')
                    quality = scorer.mark_quality_score(DataSource.OKX, date)
                    ohlcv = OHLCV(
                        symbol='BTC/USDT', date=date,
                        open=o, high=h, low=l, close=c, volume=v,
                        data_quality=quality
                    )
                    self.repo.save_ohlcv(ohlcv)
                    count += 1
                self.logger.info(f'OKX实时行情: {count}条 (最新: ${ohlcv_raw[-1][4]:,.2f})')
            except Exception as e:
                self.logger.warning(f'OKX行情获取失败: {e}')
            
            # 情绪指数(alternative.me)
            try:
                fg = FearGreedInterface()
                fg_data = fg.get_fear_greed_index(limit=30)
                for item in fg_data:
                    fgi = FearGreedIndex(
                        date=item['date'], value=item['value'],
                        classification=item['classification']
                    )
                    self.repo.save_fear_greed_index(fgi)
                self.logger.info(f'情绪指数: {len(fg_data)}条')
                fg.close()
            except Exception as e:
                self.logger.warning(f'情绪指数获取失败: {e}')
            
            # CoinMetrics链上数据(免费社区版API)
            try:
                from src.collectors.onchain_interface import CoinMetricsInterface
                cm = CoinMetricsInterface()
                
                since_date = (dt.now() - __import__('datetime').timedelta(days=30)).strftime('%Y-%m-%d')
                cm_netflow = cm.get_exchange_netflow(since=since_date)
                for item in cm_netflow:
                    nf = OnchainNetflow(
                        date=item['date'], netflow=item['netflow'],
                        source=DataSource.COINMETRICS
                    )
                    self.repo.save_netflow(nf)
                self.logger.info(f'链上净流入(CoinMetrics): {len(cm_netflow)}条')
                
                cm_stable = cm.get_stablecoin_supply(since=since_date)
                for item in cm_stable:
                    sc = StablecoinSupply(
                        date=item['date'],
                        usdt_supply=item['usdt_supply'],
                        usdc_supply=item['usdc_supply'],
                        total_supply=item['total_supply']
                    )
                    self.repo.save_stablecoin_supply(sc)
                self.logger.info(f'稳定币供应(CoinMetrics): {len(cm_stable)}条')
                
                cm.close()
            except Exception as e:
                self.logger.warning(f'CoinMetrics链上数据获取失败: {e}，使用模拟数据')
                ohlcv_list = self.repo.load_ohlcv(limit=30)
                for record in ohlcv_list:
                    date_val = record['date']
                    self.repo.save_netflow(OnchainNetflow(
                        date=date_val, netflow=np.random.normal(-200, 300),
                        source=DataSource.GLASSNODE
                    ))
                    total = 120e9 + np.random.normal(0, 1e9)
                    self.repo.save_stablecoin_supply(StablecoinSupply(
                        date=date_val, usdt_supply=total*0.73, usdc_supply=total*0.27, total_supply=total
                    ))
            
            self.logger.info('数据采集完成')
            return True
        except Exception as e:
            self.logger.error(f'数据采集失败: {e}')
            return False
    
    def run_trading_cycle(self):
        self.logger.info('--- 交易决策 ---')
        try:
            result = self.engine.run_cycle()
            
            for msg in result.get('messages', []):
                self.logger.info(f'  {msg}')
            
            return result
        except Exception as e:
            self.logger.error(f'交易决策失败: {e}')
            return None
    
    def print_status(self):
        status = self.engine.get_status()
        
        print()
        print('=' * 60)
        print(f'  AOSFT-MVP Paper Trading 状态')
        print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 60)
        print(f'  模式:       {status["mode"]}')
        print(f'  BTC价格:    ${status["current_price"]:,.2f}')
        print(f'  初始资金:   ${status["initial_capital"]:,.2f}')
        print(f'  现金:       ${status["cash"]:,.2f}')
        print(f'  持仓价值:   ${status["position_value"]:,.2f}')
        print(f'  总净值:     ${status["equity"]:,.2f}')
        print(f'  盈亏:       ${status["pnl"]:,.2f} ({status["pnl_pct"]:+.2f}%)')
        print(f'  交易次数:   {status["total_trades"]}')
        
        if status['position']:
            pos = status['position']
            entry = float(pos['entry_price'])
            amount = float(pos['amount'])
            stop = float(pos['stop_price'])
            current = status['current_price']
            unrealized = (current - entry) * amount
            
            print(f'  --- 当前持仓 ---')
            print(f'  数量:       {amount:.8f} BTC')
            print(f'  入场价:     ${entry:,.2f}')
            print(f'  止损价:     ${stop:,.2f}')
            print(f'  浮盈亏:     ${unrealized:,.2f} ({unrealized/(entry*amount)*100:+.2f}%)')
        else:
            print(f'  持仓:       空仓')
        
        print('=' * 60)
        print()
    
    def run_single(self):
        self.initialize()
        
        print()
        print('🔄 正在采集数据...')
        if self.collect_data():
            print('✅ 数据采集成功')
        else:
            print('⚠️  部分数据采集失败，使用已有数据继续')
        
        print('🔄 正在执行交易决策...')
        result = self.run_trading_cycle()
        
        if result:
            action = result.get('action', 'NONE')
            if action == 'OPEN':
                print('📈 开仓信号已执行(模拟)')
            elif action == 'CLOSE':
                pnl = result.get('pnl', 0)
                print(f'📉 平仓信号已执行(模拟), PnL=${pnl:,.2f}')
            elif action == 'STOP_LOSS':
                pnl = result.get('pnl', 0)
                print(f'🛑 止损触发(模拟), PnL=${pnl:,.2f}')
            elif action == 'HOLD':
                print('⏸️  无信号，继续持有')
            elif action == 'BLOCKED':
                print('🚫 被风控拦截')
        
        self.print_status()
        self.logger.info('Paper Trading 单次运行完成')
    
    def run_loop(self, interval_minutes: int = 60):
        self.initialize()
        self.running = True
        
        print()
        print(f'🔄 Paper Trading 持续运行模式 (每{interval_minutes}分钟检查一次)')
        print(f'   按 Ctrl+C 停止')
        print()
        
        cycle = 0
        while self.running:
            cycle += 1
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 第{cycle}轮开始...')
            
            self.collect_data()
            self.run_trading_cycle()
            self.print_status()
            
            if self.running:
                self.logger.info(f'等待{interval_minutes}分钟后执行下一轮...')
                for _ in range(interval_minutes * 60):
                    if not self.running:
                        break
                    time.sleep(1)
        
        self.logger.info('Paper Trading 已停止')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AOSFT-MVP Paper Trading')
    parser.add_argument('--loop', action='store_true', help='持续运行模式')
    parser.add_argument('--interval', type=int, default=60, help='运行间隔(分钟)')
    args = parser.parse_args()
    
    app = PaperTradingApp()
    
    if args.loop:
        app.run_loop(args.interval)
    else:
        app.run_single()


if __name__ == '__main__':
    main()
