"""
AOSFT-MVP Web UI - Streamlit监控面板
"""
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.web.service import DashboardService
from src.indicators.calculator import TechnicalIndicators
from src.regime.detector import RegimeDetector
from src.models.enums import MarketRegime
import pandas as pd


def get_process_uptime():
    try:
        result = subprocess.run(
            ["ps", "-o", "etime,pid", "-C", "python3"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:
            parts = line.strip().split()
            if len(parts) >= 2:
                return parts[0]
        return "-"
    except Exception:
        return "-"


def get_log_content(log_path: str, lines: int = 100):
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            return ''.join(content[-lines:])
    except FileNotFoundError:
        return f"日志文件不存在: {log_path}"
    except Exception as e:
        return f"读取日志失败: {e}"


st.set_page_config(
    page_title="AOSFT-MVP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = st.sidebar.text_input("数据库路径", "data/paper_trading.db")
service = DashboardService(DB_PATH)

st.sidebar.title("⚙️ 配置")
auto_refresh = st.sidebar.checkbox("自动刷新", value=False)
if auto_refresh:
    refresh_interval = st.sidebar.slider("刷新间隔(秒)", 10, 300, 60)

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")
        st.sidebar.caption(f"🔄 每{refresh_interval}s自动刷新")
    except ImportError:
        st.sidebar.warning("请安装 streamlit-autorefresh 获得最佳体验")
        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = time.time()
        elapsed = time.time() - st.session_state.last_refresh
        remaining = max(0, refresh_interval - int(elapsed))
        st.sidebar.caption(f"⏱ {remaining}s 后刷新")
        if elapsed >= refresh_interval:
            st.session_state.last_refresh = time.time()
            st.rerun()

st.sidebar.markdown("---")

uptime = get_process_uptime()
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.sidebar.markdown(f"⏰ **当前时间**: {now_str}")
st.sidebar.markdown(f"🚀 **运行时长**: {uptime}")

st.sidebar.markdown("---")
st.sidebar.markdown("**AOSFT-MVP** v1.0")
st.sidebar.markdown("链上与体制感知的BTC趋势跟踪系统")

# ========== 主页面 ==========
st.title("📊 AOSFT-MVP 监控面板")

summary = service.get_summary()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("BTC价格", f"${summary['btc_price']:,.2f}")
with col2:
    st.metric("总净值", f"${summary['equity']:,.2f}",
              f"{summary['pnl_pct']:+.2f}%")
with col3:
    st.metric("现金", f"${summary['cash']:,.2f}")
with col4:
    st.metric("持仓价值", f"${summary['position_value']:,.2f}")
with col5:
    st.metric("最大回撤", f"{summary['drawdown']*100:.2f}%")

st.markdown("---")
col_a, col_b, col_c = st.columns(3)

with col_a:
    if summary['has_position']:
        st.success("🟢 持仓中")
    else:
        st.info("⚪ 空仓")

with col_b:
    st.info(f"📈 信号数: {summary['signal_count']}")

with col_c:
    if summary['interception_count'] > 0:
        st.warning(f"🚫 风控拦截: {summary['interception_count']}次")
    else:
        st.success("🛡️ 风控正常")

# ========== 主图表区域 ==========
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 价格与信号", "💰 净值曲线", "🧠 链上指标",
     "😰 情绪指数", "📋 交易记录"]
)

# --- Tab1: 价格与信号 ---
with tab1:
    st.subheader("BTC/USDT 价格走势与交易信号")

    price_df = service.get_price_history(90)
    if not price_df.empty:
        tech = TechnicalIndicators()
        price_df = tech.calculate_all(price_df)

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('价格', '成交量', 'ATR')
        )

        fig.add_trace(go.Candlestick(
            x=price_df['date'],
            open=price_df['open'], high=price_df['high'],
            low=price_df['low'], close=price_df['close'],
            name='K线'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=price_df['date'], y=price_df['ma'],
            line=dict(color='orange', width=1.5),
            name='MA(20)'
        ), row=1, col=1)

        if 'atr' in price_df.columns:
            fig.add_trace(go.Bar(
                x=price_df['date'], y=price_df['volume'],
                name='成交量', marker_color='lightblue'
            ), row=2, col=1)

            fig.add_trace(go.Scatter(
                x=price_df['date'], y=price_df['atr'],
                line=dict(color='red', width=1),
                name='ATR(14)'
            ), row=3, col=1)

            fig.add_trace(go.Scatter(
                x=price_df['date'], y=price_df['atr_ma'],
                line=dict(color='red', width=1, dash='dash'),
                name='ATR均值(30)'
            ), row=3, col=1)

        signals_df = service.get_trade_signals(50)
        if not signals_df.empty:
            for _, sig in signals_df.iterrows():
                sig_date = sig.get('timestamp', '')[:10]
                if sig['signal_type'] == 'OPEN':
                    fig.add_trace(go.Scatter(
                        x=[sig_date], y=[sig['price']],
                        mode='markers', marker=dict(symbol='triangle-up', size=15, color='green'),
                        name='开仓', showlegend=False
                    ), row=1, col=1)
                elif sig['signal_type'] in ('CLOSE', 'STOP_LOSS', 'FORCED_CLOSE'):
                    fig.add_trace(go.Scatter(
                        x=[sig_date], y=[sig['price']],
                        mode='markers', marker=dict(symbol='triangle-down', size=15, color='red'),
                        name='平仓', showlegend=False
                    ), row=1, col=1)

        fig.update_layout(height=700, xaxis_rangeslider_visible=False)
        fig.update_xaxes(type='category', nticks=20)
        st.plotly_chart(fig, width="stretch")

        if 'ma' in price_df.columns and 'atr' in price_df.columns:
            st.subheader("市场体制识别")
            detector = RegimeDetector()
            regimes = []
            for i in range(14, len(price_df)):
                r = detector.identify(
                    close=price_df.iloc[i]['close'],
                    ma=price_df.iloc[i]['ma'],
                    atr=price_df.iloc[i]['atr'],
                    atr_ma=price_df.iloc[i]['atr_ma']
                )
                regimes.append(r.value)

            regime_df = pd.DataFrame({
                'date': price_df['date'].iloc[14:],
                'regime': regimes
            })

            regime_fig = go.Figure()
            colors = {
                MarketRegime.BULL_VOLATILE.value: 'green',
                MarketRegime.BEAR_VOLATILE.value: 'red',
                MarketRegime.LOW_VOLATILE.value: 'gray',
                MarketRegime.TRANSITIONING.value: 'orange',
            }
            for regime_type, color in colors.items():
                mask = regime_df['regime'] == regime_type
                if mask.any():
                    regime_fig.add_trace(go.Scatter(
                        x=regime_df.loc[mask, 'date'],
                        y=[regime_type] * mask.sum(),
                        mode='markers',
                        marker=dict(size=8, color=color),
                        name=regime_type
                    ))

            regime_fig.update_layout(height=200, yaxis_title='体制')
            st.plotly_chart(regime_fig, width="stretch")
    else:
        st.warning("暂无行情数据")

# --- Tab2: 净值曲线 ---
with tab2:
    st.subheader("账户净值与回撤")

    equity_df = service.get_equity_history()
    if not equity_df.empty:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            subplot_titles=('净值', '回撤')
        )

        fig.add_trace(go.Scatter(
            x=equity_df['date'], y=equity_df['equity'],
            line=dict(color='blue', width=2),
            name='净值',
            fill='tonexty'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=equity_df['date'], y=equity_df['drawdown'] * 100,
            line=dict(color='red', width=1.5),
            name='回撤(%)',
            fill='tozeroy'
        ), row=2, col=1)

        fig.add_hline(y=20, line_dash="dash", line_color="red",
                      annotation_text="熔断线(20%)", row=2, col=1)

        fig.update_layout(height=500)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("暂无净值数据")

# --- Tab3: 链上指标 ---
with tab3:
    st.subheader("交易所BTC净流入")

    netflow_df = service.get_netflow_history(30)
    if not netflow_df.empty:
        fig = go.Figure()

        netflow_ma = netflow_df['netflow'].rolling(7, min_periods=1).mean()

        fig.add_trace(go.Bar(
            x=netflow_df['date'], y=netflow_df['netflow'],
            name='净流入',
            marker_color=['green' if v < 0 else 'red' for v in netflow_df['netflow']]
        ))

        fig.add_trace(go.Scatter(
            x=netflow_df['date'], y=netflow_ma,
            line=dict(color='blue', width=2),
            name='7日均值'
        ))

        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

        st.caption("负值=BTC流出交易所(囤积信号) | 正值=BTC流入交易所(抛售信号)")
    else:
        st.info("暂无链上数据")

# --- Tab4: 情绪指数 ---
with tab4:
    st.subheader("恐惧贪婪指数")

    fg_df = service.get_fear_greed_history(30)
    if not fg_df.empty:
        fig = go.Figure()

        colors = []
        for v in fg_df['value']:
            if v <= 25: colors.append('red')
            elif v <= 45: colors.append('orange')
            elif v <= 55: colors.append('gray')
            elif v <= 75: colors.append('lightgreen')
            else: colors.append('green')

        fig.add_trace(go.Bar(
            x=fg_df['date'], y=fg_df['value'],
            marker_color=colors,
            name='Fear & Greed'
        ))

        fig.add_hline(y=80, line_dash="dash", line_color="red",
                      annotation_text="开仓上限(80)")

        fig.update_layout(height=400, yaxis_range=[0, 100])
        st.plotly_chart(fig, width="stretch")

        current = fg_df.iloc[-1]
        col_f1, col_f2 = st.columns(2)
        col_f1.metric("当前值", f"{int(current['value'])}")
        col_f2.metric("分类", current['classification'])
    else:
        st.info("暂无情绪数据")

# --- Tab5: 交易记录 ---
with tab5:
    st.subheader("交易信号记录")

    signals_df = service.get_trade_signals(50)
    if not signals_df.empty:
        display_df = signals_df[['timestamp', 'signal_type', 'symbol', 'price', 'regime', 'reason']].copy()
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, width="stretch", hide_index=True)
    else:
        st.info("暂无交易信号")

    st.subheader("已平仓记录")
    closed_df = service.get_closed_positions()
    if not closed_df.empty:
        display_df = closed_df[['entry_time', 'entry_price', 'exit_time', 'exit_price',
                                'amount', 'pnl', 'exit_reason']].copy()
        display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
        display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}" if x else "-")
        display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}" if x else "-")
        st.dataframe(display_df, width="stretch", hide_index=True)
    else:
        st.info("暂无已平仓记录")

    st.subheader("风控拦截记录")
    risk_df = service.get_risk_interceptions(20)
    if not risk_df.empty:
        display_df = risk_df[['timestamp', 'interception_type', 'action_taken', 'reason']].copy()
        st.dataframe(display_df, width="stretch", hide_index=True)
    else:
        st.success("无风控拦截记录")

# ========== 底部：系统配置 ==========
st.markdown("---")
with st.expander("🔧 系统配置参数"):
    config_df = service.get_system_config()
    if not config_df.empty:
        st.dataframe(config_df, width="stretch", hide_index=True)

# ========== 底部：日志查看 ==========
with st.expander("📋 运行日志"):
    log_col1, log_col2, log_col3 = st.columns([2, 1, 1])
    with log_col1:
        log_file = st.selectbox(
            "选择日志文件",
            ["logs/paper_trading.log", "logs/webui.log", "logs/aosft.log"],
            index=0
        )
    with log_col2:
        log_lines = st.number_input("显示行数", min_value=50, max_value=1000, value=100, step=50)
    with log_col3:
        log_auto_refresh = st.checkbox("日志自动刷新", value=False)
        if log_auto_refresh:
            log_refresh_interval = st.number_input("刷新间隔(秒)", min_value=5, max_value=60, value=10)

    if log_auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=log_refresh_interval * 1000, key="logrefresh")
        except ImportError:
            pass

    log_content = get_log_content(log_file, log_lines)
    st.code(log_content, language="text")
