# AOSFT-MVP API接口文档

## 1. OKX交易所接口

### 1.1 行情数据接口 (OKXMarketInterface)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `fetch_ohlcv(symbol, timeframe, limit)` | 获取K线数据 | symbol: 交易对(默认BTC/USDT), timeframe: 周期(默认1d), limit: 数量(默认100) | pd.DataFrame |
| `fetch_ticker(symbol)` | 获取最新价格 | symbol: 交易对 | dict(last, bid, ask, high, low, volume) |

### 1.2 交易执行接口 (OKXTradingInterface)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `create_limit_order(symbol, side, amount, price)` | 创建限价单 | symbol, side(buy/sell), amount, price | dict(id, status, ...) |
| `create_market_order(symbol, side, amount)` | 创建市价单 | symbol, side, amount | dict |
| `cancel_order(order_id, symbol)` | 撤销订单 | order_id, symbol | dict |
| `fetch_order(order_id, symbol)` | 查询订单 | order_id, symbol | dict |
| `fetch_balance()` | 查询余额 | - | dict(total, free, used) |
| `fetch_funding_rate(symbol)` | 查询资金费率 | symbol | float |

## 2. 链上数据接口

### 2.1 Glassnode接口 (GlassnodeInterface)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_exchange_netflow(asset, since, until)` | 获取交易所净流入 | asset(BTC), since, until(日期) | List[dict(date, netflow)] |

### 2.2 CryptoQuant接口 (CryptoQuantInterface)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_exchange_netflow(exchange, since, until)` | 获取交易所净流入 | exchange, since, until | List[dict] |

## 3. 其他数据源接口

### 3.1 CoinGecko接口 (CoinGeckoInterface)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_stablecoin_supply(days)` | 获取稳定币供应量 | days: 天数 | List[dict(date, usdt_supply, usdc_supply, total_supply)] |

### 3.2 恐惧贪婪指数接口 (FearGreedInterface)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_fear_greed_index(limit)` | 获取情绪指数 | limit: 天数 | List[dict(date, value, classification)] |

### 3.3 Telegram通知接口 (TelegramNotifier)

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `send_message(text)` | 发送消息 | text: 消息内容 | bool |
| `notify_trade(action, symbol, amount, price)` | 交易通知 | action, symbol, amount, price | bool |
| `notify_alert(alert_type, message, severity)` | 告警通知 | alert_type, message, severity | bool |
| `notify_daily_report(equity, position, drawdown)` | 每日报告 | equity, position, drawdown | bool |

## 4. 内部模块接口

### 4.1 数据仓库 (DataRepository)

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `save_ohlcv(data)` / `load_ohlcv(symbol, start_date, end_date)` | 日线数据CRUD | int / List[dict] |
| `save_netflow(data)` / `load_netflow(days)` | 链上数据CRUD | int / List[dict] |
| `save_stablecoin_supply(data)` / `load_stablecoin_supply(days)` | 稳定币数据CRUD | int / List[dict] |
| `save_signal(data)` / `load_signals(limit)` | 交易信号CRUD | int / List[dict] |
| `save_position(data)` / `load_current_position()` | 持仓CRUD | int / dict |
| `save_equity(data)` / `get_latest_equity()` | 净值CRUD | int / dict |
| `save_order(data)` / `update_order_status(...)` | 订单CRUD | int / bool |
| `save_interception(data)` | 风控拦截记录 | int |
| `save_circuit_breaker_event(data)` / `get_active_circuit_breaker()` | 熔断事件CRUD | int / dict |
| `get_config(key)` / `set_config(key, value)` | 系统配置CRUD | str / bool |

### 4.2 策略引擎 (StrategyEngine)

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `run_daily()` | 执行每日策略决策 | Optional[TradeSignal] |

### 4.3 风控拦截器 (RiskInterceptor)

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `intercept(signal)` | 拦截检查(一票否决权) | dict(passed, action, reason) |
| `quick_check()` | 快速检查(熔断+数据新鲜度) | bool |

### 4.4 执行网关 (ExecutionGateway)

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `execute_open(signal, amount)` | 执行开仓 | Optional[dict] |
| `execute_close(signal, amount)` | 执行平仓 | Optional[dict] |
| `check_and_recover_orders()` | 检查并恢复异常订单 | None |

### 4.5 回测引擎 (BacktestEngine)

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `run(ohlcv_df, netflow_df, stablecoin_df, fg_df)` | 运行回测 | BacktestResult |

## 5. 环境变量配置

| 变量 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `OKX_API_KEY` | 是 | OKX API密钥 | - |
| `OKX_SECRET` | 是 | OKX Secret密钥 | - |
| `OKX_PASSWORD` | 是 | OKX密码 | - |
| `GLASSNODE_API_KEY` | 否 | Glassnode API密钥 | - |
| `TELEGRAM_BOT_TOKEN` | 否 | Telegram Bot Token | - |
| `TELEGRAM_CHAT_ID` | 否 | Telegram Chat ID | - |
| `DATABASE_PATH` | 否 | 数据库路径 | data/aosft.db |
| `LOG_LEVEL` | 否 | 日志级别 | INFO |
| `MA_PERIOD` | 否 | 趋势均线周期 | 20 |
| `ATR_PERIOD` | 否 | ATR计算周期 | 14 |
| `STOP_ATR_MULTIPLIER` | 否 | 止损ATR倍数 | 2.0 |
| `POSITION_RATIO` | 否 | 仓位占比 | 0.5 |
| `MAX_DRAWDOWN_GLOBAL` | 否 | 全局最大回撤 | 0.20 |
