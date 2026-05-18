"""
AOSFT-MVP Web UI - Streamlit监控面板
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.web.service import DashboardService
from src.indicators.calculator import TechnicalIndicators
from src.regime.detector import RegimeDetector
import pandas as pd

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
    st.empty()

st.sidebar.markdown("---")
st.sidebar.markdown("**AOSFT-MVP** v1.0")
st.sidebar.markdown("链上与体制感知的BTC趋势跟踪系统")

# ========== 主页面 ==========
st.title("📊 AOSFT-MVP 监控面板")

summary = service.get_summary()

# 顶部指标卡片
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

# 状态指示器
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
        
        # 标记交易信号
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
        st.plotly_chart(fig, use_container_width=True)
        
        # 体制识别
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
            colors = {'BULL_VOLATILE': 'green', 'BEAR_VOLATILE': 'red', 'LOW_VOLATILE': 'gray'}
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
            st.plotly_chart(regime_fig, use_container_width=True)
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
        st.plotly_chart(fig, use_container_width=True)
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
        st.plotly_chart(fig, use_container_width=True)
        
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
        st.plotly_chart(fig, use_container_width=True)
        
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
        st.dataframe(display_df, use_container_width=True, hide_index=True)
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
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无已平仓记录")
    
    st.subheader("风控拦截记录")
    risk_df = service.get_risk_interceptions(20)
    if not risk_df.empty:
        display_df = risk_df[['timestamp', 'interception_type', 'action_taken', 'reason']].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.success("无风控拦截记录")

# ========== 底部：系统配置 ==========
st.markdown("---")
with st.expander("🔧 系统配置参数"):
    config_df = service.get_system_config()
    if not config_df.empty:
        st.dataframe(config_df, use_container_width=True, hide_index=True)
