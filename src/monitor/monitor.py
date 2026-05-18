"""
监控告警模块
实时监控和通知
"""
import logging
from datetime import datetime
from typing import Optional
from ..models.repository import DataRepository
from ..models.enums import PositionStatus
from ..collectors.data_source_interface import TelegramNotifier

logger = logging.getLogger("aosft")


class Monitor:
    def __init__(self, repo: DataRepository, notifier: Optional[TelegramNotifier] = None):
        self.repo = repo
        self.notifier = notifier
    
    def update_data_freshness_metrics(self):
        from ..risk.data_freshness_checker import DataFreshnessChecker
        checker = DataFreshnessChecker(self.repo)
        result = checker.check_and_alert()
        
        for source_name, info in result.get('freshness', {}).items():
            if source_name == 'all_fresh':
                continue
            self.repo.save_metric(
                metric_type='DATA_FRESHNESS',
                metric_name=f'{source_name}_delay_days',
                value=info.get('delay_days', 0),
                unit='days'
            )
    
    def update_strategy_performance_metrics(self):
        signals = self.repo.load_signals(limit=100)
        
        open_signals = [s for s in signals if s['signal_type'] == 'OPEN']
        close_signals = [s for s in signals if s['signal_type'] in ('CLOSE', 'STOP_LOSS', 'FORCED_CLOSE')]
        
        positions = []
        with self.repo._get_conn() as conn:
            rows = conn.execute("SELECT * FROM positions WHERE status = 'CLOSED'").fetchall()
            positions = [dict(r) for r in rows]
        
        if positions:
            wins = sum(1 for p in positions if p.get('pnl', 0) > 0)
            win_rate = wins / len(positions)
            
            total_pnl = sum(p.get('pnl', 0) for p in positions)
            losses = [p.get('pnl', 0) for p in positions if p.get('pnl', 0) < 0]
            wins_pnl = [p.get('pnl', 0) for p in positions if p.get('pnl', 0) > 0]
            
            avg_win = sum(wins_pnl) / len(wins_pnl) if wins_pnl else 0
            avg_loss = abs(sum(losses) / len(losses)) if losses else 1
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            
            consecutive_losses = 0
            max_consecutive = 0
            for p in positions:
                if p.get('pnl', 0) < 0:
                    consecutive_losses += 1
                    max_consecutive = max(max_consecutive, consecutive_losses)
                else:
                    consecutive_losses = 0
            
            self.repo.save_metric('STRATEGY_PERFORMANCE', 'win_rate', win_rate, '%')
            self.repo.save_metric('STRATEGY_PERFORMANCE', 'profit_factor', profit_factor)
            self.repo.save_metric('STRATEGY_PERFORMANCE', 'total_trades', len(positions))
            self.repo.save_metric('STRATEGY_PERFORMANCE', 'max_consecutive_losses', max_consecutive)
    
    def update_risk_stats_metrics(self):
        with self.repo._get_conn() as conn:
            interception_count = conn.execute("""
                SELECT COUNT(*) as cnt FROM risk_interceptions
                WHERE date(created_at) = date('now')
            """).fetchone()['cnt']
            
            breaker_count = conn.execute("""
                SELECT COUNT(*) as cnt FROM circuit_breaker_events
            """).fetchone()['cnt']
        
        self.repo.save_metric('RISK_STATS', 'daily_interceptions', interception_count)
        self.repo.save_metric('RISK_STATS', 'total_breaker_events', breaker_count)
    
    def update_api_stats_metrics(self):
        last_updates = self.repo.timestamp_manager.get_all_last_update_times()
        for source, info in last_updates.items():
            self.repo.save_metric(
                'API_STATS', f'{source}_last_update',
                0, unit='timestamp',
                metadata={'last_update': info['last_update']}
            )
    
    def send_daily_report(self):
        equity = self.repo.get_latest_equity()
        position = self.repo.load_current_position()
        
        if not equity:
            return
        
        drawdown = equity.get('drawdown', 0)
        
        if self.notifier:
            self.notifier.notify_daily_report(
                equity=equity['equity'],
                position=position,
                drawdown=drawdown
            )
        
        logger.info(
            f"[MONITOR] 每日报告: equity={equity['equity']:.2f} "
            f"drawdown={drawdown*100:.2f}%"
        )
