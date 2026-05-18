"""
回测报告生成器
生成Markdown格式的回测报告
"""
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path
from ..backtest.engine import BacktestResult

logger = logging.getLogger("aosft")


class BacktestReportGenerator:
    def __init__(self, output_dir: str = "backtests/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, result: BacktestResult, strategy_name: str = "AOSFT-MVP") -> str:
        now = datetime.now()
        filename = f"backtest_{strategy_name}_{now.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        content = self._build_report(result, strategy_name, now)
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"[BACKTEST-REPORT] 报告已生成: {filepath}")
        return str(filepath)
    
    def _build_report(self, result: BacktestResult, strategy_name: str, now: datetime) -> str:
        lines = [
            f"# {strategy_name} 回测报告",
            f"",
            f"**生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"---",
            f"",
            f"## 1. 总体表现",
            f"",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 初始资金 | ${result.initial_capital:,.2f} |",
            f"| 最终资金 | ${result.final_capital:,.2f} |",
            f"| 总收益率 | {result.total_return*100:.2f}% |",
            f"| 年化收益率 | {result.annual_return*100:.2f}% |",
            f"| 最大回撤 | {result.max_drawdown*100:.2f}% |",
            f"| 夏普比率 | {result.sharpe_ratio:.2f} |",
            f"| 卡尔玛比率 | {result.annual_return/result.max_drawdown:.2f} |" if result.max_drawdown > 0 else f"| 卡尔玛比率 | N/A |",
            f"",
            f"## 2. 交易统计",
            f"",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总交易次数 | {result.total_trades} |",
            f"| 胜率 | {result.win_rate*100:.1f}% |",
            f"| 盈亏比 | {result.profit_factor:.2f} |",
            f"| 最大连续亏损 | {result.max_consecutive_losses}次 |",
            f"",
        ]
        
        if result.trades:
            lines.extend([
                f"## 3. 交易明细",
                f"",
                f"| # | 入场日期 | 入场价格 | 离场日期 | 离场价格 | 盈亏 | 盈亏% | 原因 |",
                f"|--|---------|---------|---------|---------|------|------|------|",
            ])
            
            for i, trade in enumerate(result.trades, 1):
                lines.append(
                    f"| {i} | {trade.entry_date} | ${trade.entry_price:,.2f} | "
                    f"{trade.exit_date} | ${trade.exit_price:,.2f} | "
                    f"${trade.pnl:,.2f} | {trade.pnl_pct*100:.2f}% | "
                    f"{trade.exit_reason} |"
                )
            
            lines.append(f"")
        
        lines.extend([
            f"---",
            f"",
            f"*报告由AOSFT-MVP回测系统自动生成*",
        ])
        
        return "\n".join(lines)
