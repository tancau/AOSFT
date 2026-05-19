# AOSFT-MVP 编码任务规划

**版本**: v2.0  
**项目名称**: AOSFT-MVP — 链上与体制感知的BTC趋势跟踪系统  
**生成日期**: 2026-05-19  
**更新说明**: 根据设计方案重大更新,新增风控前置拦截、数据质量评分、订单状态机、分级熔断恢复、完整监控指标体系等模块

---

## 1. 数据时间戳管理和质量评分模块 (新增)

### 1.1 数据时间戳管理器
- [ ] 创建数据时间戳管理模块 `src/models/data_timestamp_manager.py`
- [ ] 实现 `DataTimestampManager` 类
- [ ] 实现 `mark_collection_time()` 方法,为每个数据点标记实际采集时间和数据日期
- [ ] 实现 `calculate_freshness()` 方法,计算数据新鲜度(距当前时间的延迟天数)
- [ ] 实现 `get_last_update_time()` 方法,获取各数据源最后更新时间
- [ ] 实现数据时间戳持久化到数据库 `data_timestamps` 表
- [ ] 编写单元测试 `tests/unit/test_data_timestamp_manager.py`
- **涉及文件**: `src/models/data_timestamp_manager.py`, `tests/unit/test_data_timestamp_manager.py`
- **技术要点**: 时间戳计算、延迟天数统计、数据库持久化
- **验收标准**: 数据时间戳正确标记,新鲜度计算准确
- **预估工时**: 2小时
- **依赖关系**: 无(基础设施已实现)

### 1.2 数据质量评分器
- [ ] 创建数据质量评分模块 `src/models/data_quality_scorer.py`
- [ ] 实现 `DataQualityScorer` 类
- [ ] 实现 `calculate_score()` 方法,根据数据延迟天数计算质量评分
  - 延迟≤1天: 评分=1.0(满分)
  - 延迟=2天: 评分=0.8
  - 延迟≥3天: 评分=0.5并记录告警
- [ ] 实现 `mark_quality_score()` 方法,标记数据质量评分
- [ ] 实现 `get_quality_score()` 方法,查询指定数据的质量评分
- [ ] 编写单元测试 `tests/unit/test_data_quality_scorer.py`
- **涉及文件**: `src/models/data_quality_scorer.py`, `tests/unit/test_data_quality_scorer.py`
- **技术要点**: 分级评分逻辑、告警触发
- **验收标准**: 质量评分计算正确,告警正确触发
- **预估工时**: 1.5小时
- **依赖关系**: 1.1

### 1.3 数据质量集成到数据仓库
- [ ] 扩展数据仓库 `src/models/repository.py`,集成时间戳管理和质量评分
- [ ] 在保存数据时自动标记采集时间和计算质量评分
- [ ] 在读取数据时自动附加质量评分信息
- [ ] 实现按质量评分过滤数据的功能
- [ ] 编写集成测试 `tests/unit/test_repository_with_quality.py`
- **涉及文件**: `src/models/repository.py`, `tests/unit/test_repository_with_quality.py`
- **技术要点**: 数据质量集成、过滤逻辑
- **验收标准**: 数据保存和读取自动处理质量评分
- **预估工时**: 2小时
- **依赖关系**: 1.2

---

## 2. 风控前置拦截模块 (新增)

### 2.1 熔断状态检查器
- [ ] 创建熔断状态检查模块 `src/risk/circuit_breaker_checker.py`
- [ ] 实现 `CircuitBreakerChecker` 类
- [ ] 实现 `check_circuit_breaker_status()` 方法,检查当前是否处于熔断暂停期
- [ ] 实现 `get_circuit_breaker_info()` 方法,获取熔断详细信息(类型、触发时间、恢复时间)
- [ ] 实现熔断状态查询优化(缓存机制)
- [ ] 编写单元测试 `tests/unit/test_circuit_breaker_checker.py`
- **涉及文件**: `src/risk/circuit_breaker_checker.py`, `tests/unit/test_circuit_breaker_checker.py`
- **技术要点**: 熔断状态查询、缓存优化
- **验收标准**: 熔断状态检查准确快速
- **预估工时**: 1.5小时
- **依赖关系**: 无

### 2.2 数据新鲜度检查器
- [ ] 创建数据新鲜度检查模块 `src/risk/data_freshness_checker.py`
- [ ] 实现 `DataFreshnessChecker` 类
- [ ] 实现 `check_data_freshness()` 方法,检查所有依赖数据的新鲜度
- [ ] 实现 `get_stale_data_sources()` 方法,返回过期数据源列表
- [ ] 实现新鲜度阈值检查(默认≥3天视为过期)
- [ ] 实现新鲜度告警推送
- [ ] 编写单元测试 `tests/unit/test_data_freshness_checker.py`
- **涉及文件**: `src/risk/data_freshness_checker.py`, `tests/unit/test_data_freshness_checker.py`
- **技术要点**: 新鲜度检查、过期数据源识别
- **验收标准**: 数据新鲜度检查准确,过期告警正确触发
- **预估工时**: 1.5小时
- **依赖关系**: 1.1

### 2.3 市场异常检查器
- [ ] 创建市场异常检查模块 `src/risk/market_anomaly_checker.py`
- [ ] 实现 `MarketAnomalyChecker` 类
- [ ] 实现 `check_market_anomaly()` 方法,检查市场是否出现异常波动
- [ ] 实现异常波动检测逻辑:
  - 当日波动(最高价-最低价)/开盘价 > 10%
  - 15分钟跌幅 ≥ 5%
  - 24小时跌幅 ≥ 15%
- [ ] 实现 `get_anomaly_details()` 方法,返回异常详情
- [ ] 编写单元测试 `tests/unit/test_market_anomaly_checker.py`
- **涉及文件**: `src/risk/market_anomaly_checker.py`, `tests/unit/test_market_anomaly_checker.py`
- **技术要点**: 市场波动计算、异常阈值检测
- **验收标准**: 市场异常检测准确
- **预估工时**: 1.5小时
- **依赖关系**: 无

### 2.4 风控前置拦截器核心
- [ ] 创建风控拦截器核心模块 `src/risk/risk_interceptor.py`
- [ ] 实现 `RiskInterceptor` 类
- [ ] 实现 `intercept()` 方法,执行完整风控拦截检查流程
- [ ] 集成熔断状态检查、数据新鲜度检查、市场异常检查
- [ ] 实现一票否决权逻辑:
  - 任一检查未通过 → 拦截信号并记录否决原因
  - 所有检查通过 → 允许信号传递到执行层
- [ ] 实现 `record_veto_reason()` 方法,记录拦截原因到数据库 `risk_interceptions` 表
- [ ] 实现 `get_interception_history()` 方法,查询拦截历史
- [ ] 编写单元测试 `tests/unit/test_risk_interceptor.py`
- **涉及文件**: `src/risk/risk_interceptor.py`, `tests/unit/test_risk_interceptor.py`
- **技术要点**: 拦截逻辑、一票否决权、原因记录
- **验收标准**: 风控拦截逻辑正确,拦截原因准确记录
- **预估工时**: 2.5小时
- **依赖关系**: 2.1, 2.2, 2.3

---

## 3. 数据采集模块开发

### 3.1 数据采集器基类(增强)
- [ ] 扩展数据采集器基类 `src/collectors/base_collector.py`
- [ ] 在 `save_to_db()` 方法中集成时间戳标记和质量评分
- [ ] 实现数据新鲜度检查逻辑
- [ ] 实现数据过期告警推送
- [ ] 编写单元测试验证增强功能
- **涉及文件**: `src/collectors/base_collector.py`
- **技术要点**: 时间戳集成、质量评分集成
- **验收标准**: 数据采集自动标记时间戳和质量评分
- **预估工时**: 1小时
- **依赖关系**: 1.3

### 3.2 OKX行情数据采集器
- [ ] 创建OKX采集器 `src/collectors/ohlcv_collector.py`
- [ ] 实现 `OHLCVCollector` 类,继承 `BaseCollector`
- [ ] 实现 `collect()` 方法,调用OKX API获取日线数据
- [ ] 实现数据完整性校验(价格>0,交易量>0)
- [ ] 实现异常数据处理(使用前一日数据)
- [ ] 实现数据时间戳标记和质量评分
- [ ] 编写单元测试 `tests/unit/test_ohlcv_collector.py`
- **涉及文件**: `src/collectors/ohlcv_collector.py`, `tests/unit/test_ohlcv_collector.py`
- **验收标准**: 日线数据正确采集并保存,时间戳和质量评分正确标记
- **预估工时**: 1.5小时
- **依赖关系**: 3.1

### 3.3 链上数据采集器
- [ ] 创建链上采集器 `src/collectors/netflow_collector.py`
- [ ] 实现 `NetflowCollector` 类
- [ ] 实现从Glassnode/CryptoQuant获取净流入数据
- [ ] 实现数据延迟处理(shift(2))
- [ ] 实现数据源降级处理(主数据源失败时使用备用源)
- [ ] 实现数据时间戳标记和质量评分
- [ ] 编写单元测试 `tests/unit/test_netflow_collector.py`
- **涉及文件**: `src/collectors/netflow_collector.py`, `tests/unit/test_netflow_collector.py`
- **验收标准**: 链上数据正确采集,延迟处理和时间戳标记正确
- **预估工时**: 1.5小时
- **依赖关系**: 3.1

### 3.4 稳定币数据采集器
- [ ] 创建稳定币采集器 `src/collectors/stablecoin_collector.py`
- [ ] 实现 `StablecoinCollector` 类
- [ ] 实现从CoinGecko获取稳定币供应数据
- [ ] 实现7日变化量计算
- [ ] 实现数据时间戳标记和质量评分
- [ ] 编写单元测试 `tests/unit/test_stablecoin_collector.py`
- **涉及文件**: `src/collectors/stablecoin_collector.py`, `tests/unit/test_stablecoin_collector.py`
- **验收标准**: 稳定币数据正确采集,变化量计算正确
- **预估工时**: 1小时
- **依赖关系**: 3.1

### 3.5 情绪指数采集器
- [ ] 创建情绪指数采集器 `src/collectors/sentiment_collector.py`
- [ ] 实现 `SentimentCollector` 类
- [ ] 实现从alternative.me获取情绪指数
- [ ] 实现数据时间戳标记和质量评分
- [ ] 编写单元测试 `tests/unit/test_sentiment_collector.py`
- **涉及文件**: `src/collectors/sentiment_collector.py`, `tests/unit/test_sentiment_collector.py`
- **验收标准**: 情绪指数正确采集并保存
- **预估工时**: 1小时
- **依赖关系**: 3.1

### 3.6 数据采集协调器
- [ ] 创建数据采集协调器 `src/collectors/data_collector.py`
- [ ] 实现 `DataCollector` 类,协调所有采集器
- [ ] 实现 `run_daily_collection()` 方法,执行每日数据采集流程
- [ ] 实现数据完整性校验,检查所有数据源是否采集成功
- [ ] 实现采集失败告警通知
- [ ] 实现采集性能监控(5分钟内完成)
- [ ] 实现数据新鲜度统计和质量评分汇总
- [ ] 编写协调器单元测试 `tests/unit/test_data_collector.py`
- **涉及文件**: `src/collectors/data_collector.py`, `tests/unit/test_data_collector.py`
- **验收标准**: 所有数据源正确采集,异常情况正确处理和告警
- **预估工时**: 2小时
- **依赖关系**: 3.2, 3.3, 3.4, 3.5

---

## 4. 外部API接口封装层

### 4.1 OKX交易所接口封装
- [ ] 创建OKX接口模块 `src/collectors/okx_interface.py`
- [ ] 实现 `OKXMarketInterface` 类,封装行情数据查询接口
- [ ] 实现 `fetch_ohlcv()` 方法,获取日线K线数据(返回Pandas DataFrame)
- [ ] 实现 `fetch_ticker()` 方法,获取最新价格信息
- [ ] 实现 `OKXTradingInterface` 类,封装交易执行接口
- [ ] 实现 `create_limit_order()` 方法,创建限价单
- [ ] 实现 `create_market_order()` 方法,创建市价单,支持滑点容忍设置
- [ ] 实现 `cancel_order()` 方法,撤销订单
- [ ] 实现 `fetch_order()` 方法,查询订单状态
- [ ] 实现 `fetch_balance()` 方法,查询账户余额
- [ ] 实现 `fetch_positions()` 方法,查询持仓信息(永续合约)
- [ ] 实现 `fetch_funding_rate()` 方法,查询资金费率(永续合约)
- [ ] 实现API调用重试和超时机制
- [ ] 编写OKX接口单元测试 `tests/unit/test_okx_interface.py`
- **涉及文件**: `src/collectors/okx_interface.py`, `tests/unit/test_okx_interface.py`
- **技术要点**: CCXT库,异常处理,重试机制,DataFrame转换
- **验收标准**: OKX API调用成功,数据格式正确,异常情况正确处理
- **预估工时**: 3小时
- **依赖关系**: 无

### 4.2 链上数据接口封装
- [ ] 创建链上接口模块 `src/collectors/onchain_interface.py`
- [ ] 实现 `GlassnodeInterface` 类
- [ ] 实现 `get_exchange_netflow()` 方法,获取交易所BTC净流入数据
- [ ] 实现 `CryptoQuantInterface` 类(备选数据源)
- [ ] 实现数据延迟shift(2)处理,确保不使用未来信息
- [ ] 实现API调用重试和异常处理
- [ ] 编写链上接口单元测试 `tests/unit/test_onchain_interface.py`
- **涉及文件**: `src/collectors/onchain_interface.py`, `tests/unit/test_onchain_interface.py`
- **技术要点**: Requests库,API认证,数据延迟处理
- **验收标准**: 链上数据获取成功,数据延迟正确应用
- **预估工时**: 2小时
- **依赖关系**: 无

### 4.3 稳定币数据接口封装
- [ ] 创建稳定币接口模块 `src/collectors/stablecoin_interface.py`
- [ ] 实现 `CoinGeckoInterface` 类
- [ ] 实现 `get_stablecoin_supply()` 方法,获取USDT和USDC供应量
- [ ] 实现7日变化率计算逻辑
- [ ] 编写稳定币接口单元测试 `tests/unit/test_stablecoin_interface.py`
- **涉及文件**: `src/collectors/stablecoin_interface.py`, `tests/unit/test_stablecoin_interface.py`
- **验收标准**: 稳定币数据获取成功,变化率计算正确
- **预估工时**: 1小时
- **依赖关系**: 无

### 4.4 情绪指数接口封装
- [ ] 创建情绪指数接口模块 `src/collectors/sentiment_interface.py`
- [ ] 实现 `FearGreedIndexInterface` 类
- [ ] 实现 `get_index()` 方法,获取Crypto Fear & Greed Index
- [ ] 实现分类标签映射逻辑(Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- [ ] 编写情绪指数接口单元测试 `tests/unit/test_sentiment_interface.py`
- **涉及文件**: `src/collectors/sentiment_interface.py`, `tests/unit/test_sentiment_interface.py`
- **验收标准**: 情绪指数获取成功,分类标签正确映射
- **预估工时**: 1小时
- **依赖关系**: 无

### 4.5 Telegram通知接口封装
- [ ] 创建Telegram接口模块 `src/monitor/telegram_interface.py`
- [ ] 实现 `TelegramInterface` 类
- [ ] 实现 `send_trade_notification()` 方法,发送交易通知
- [ ] 实现 `send_alert()` 方法,发送告警消息
- [ ] 实现敏感数据过滤功能 `filter_sensitive_data()`
- [ ] 实现推送失败处理(不影响主流程)
- [ ] 编写Telegram接口单元测试 `tests/unit/test_telegram_interface.py`
- **涉及文件**: `src/monitor/telegram_interface.py`, `tests/unit/test_telegram_interface.py`
- **技术要点**: python-telegram-bot库,异步消息发送
- **验收标准**: Telegram消息成功发送,敏感数据已过滤
- **预估工时**: 1.5小时
- **依赖关系**: 无

---

## 5. 指标计算模块开发

### 5.1 技术指标计算器
- [ ] 创建指标计算模块 `src/indicators/technical_indicators.py`
- [ ] 实现 `TechnicalIndicators` 类
- [ ] 实现 `calculate_ma()` 方法,计算移动平均线MA(20)
- [ ] 实现 `calculate_atr()` 方法,计算平均真实波动幅度ATR(14)
- [ ] 实现 `calculate_atr_ma()` 方法,计算ATR的30日移动平均值
- [ ] 实现边界条件处理(历史数据不足情况)
- [ ] 编写技术指标计算单元测试 `tests/unit/test_technical_indicators.py`
- **涉及文件**: `src/indicators/technical_indicators.py`, `tests/unit/test_technical_indicators.py`
- **技术要点**: Pandas滚动计算,NumPy数组运算
- **验收标准**: 技术指标计算正确,与标准公式一致
- **预估工时**: 2小时
- **依赖关系**: 无

### 5.2 链上指标计算器
- [ ] 创建链上指标模块 `src/indicators/onchain_indicators.py`
- [ ] 实现 `OnchainIndicators` 类
- [ ] 实现 `calculate_netflow_trend()` 方法,计算净流入7日均值
- [ ] 实现 `calculate_stablecoin_change()` 方法,计算稳定币7日变化量
- [ ] 实现连续信号检测逻辑(连续3日满足条件)
- [ ] 编写链上指标计算单元测试 `tests/unit/test_onchain_indicators.py`
- **涉及文件**: `src/indicators/onchain_indicators.py`, `tests/unit/test_onchain_indicators.py`
- **验收标准**: 链上指标计算正确,连续信号检测正确
- **预估工时**: 1.5小时
- **依赖关系**: 无

---

## 6. 体制识别模块开发

### 6.1 市场体制识别器
- [ ] 创建体制识别模块 `src/regime/regime_detector.py`
- [ ] 实现 `RegimeDetector` 类
- [ ] 实现 `detect_regime()` 方法,根据技术指标判断市场体制
- [ ] 实现BULL_VOLATILE判定逻辑:收盘价>MA(20)且ATR(14)>ATR均线
- [ ] 实现BEAR_VOLATILE判定逻辑:收盘价≤MA(20)且ATR(14)>ATR均线
- [ ] 实现LOW_VOLATILE判定逻辑:ATR(14)≤ATR均线
- [ ] 编写体制识别单元测试 `tests/unit/test_regime_detector.py`
- **涉及文件**: `src/regime/regime_detector.py`, `tests/unit/test_regime_detector.py`
- **验收标准**: 市场体制识别正确,符合需求规则定义
- **预估工时**: 1.5小时
- **依赖关系**: 5.1

---

## 7. 信号生成模块开发

### 7.1 信号生成器
- [ ] 创建信号生成模块 `src/signals/signal_generator.py`
- [ ] 实现 `SignalGenerator` 类
- [ ] 实现 `generate_open_signal()` 方法,检查开仓条件
- [ ] 开仓条件:体制BULL_VOLATILE,净流入均值<0,稳定币变化>0,情绪指数<80
- [ ] 实现 `generate_close_signal()` 方法,检查平仓条件
- [ ] 平仓条件1:体制转为BEAR_VOLATILE
- [ ] 平仓条件2:净流入均值连续3日>0
- [ ] 平仓条件3:稳定币变化连续3日<0
- [ ] 实现 `generate_stop_loss_signal()` 方法,检查硬止损触发
- [ ] 硬止损条件:当前价格≤入场价-2×ATR(14)
- [ ] 实现 `generate_signals()` 方法,综合生成所有信号
- [ ] 编写信号生成单元测试 `tests/unit/test_signal_generator.py`
- **涉及文件**: `src/signals/signal_generator.py`, `tests/unit/test_signal_generator.py`
- **验收标准**: 信号生成逻辑正确,所有条件正确检查
- **预估工时**: 2.5小时
- **依赖关系**: 6.1, 5.2

---

## 8. 策略决策引擎开发

### 8.1 仓位管理器
- [ ] 创建仓位管理模块 `src/strategy/position_manager.py`
- [ ] 实现 `PositionManager` 类
- [ ] 实现 `calculate_position_size()` 方法,计算开仓金额
- [ ] 仓位计算:账户净值×50%,风险控制止损亏损≤5%
- [ ] 实现 `calculate_stop_loss()` 方法,计算止损价格
- [ ] 止损价=入场价-2×ATR(14),止损价只升不降
- [ ] 实现 `update_stop_loss()` 方法,每4小时更新止损价
- [ ] 编写仓位管理单元测试 `tests/unit/test_position_manager.py`
- **涉及文件**: `src/strategy/position_manager.py`, `tests/unit/test_position_manager.py`
- **验收标准**: 仓位计算正确,止损价格计算正确
- **预估工时**: 2小时
- **依赖关系**: 5.1

### 8.2 交易频率控制器
- [ ] 创建频率控制模块 `src/strategy/frequency_controller.py`
- [ ] 实现 `FrequencyController` 类
- [ ] 实现已持仓禁止新开仓逻辑
- [ ] 实现平仓后至少1日才能开仓逻辑
- [ ] 实现合约模式资金费率检查(资金费率<-0.1%暂不开仓)
- [ ] 编写频率控制单元测试 `tests/unit/test_frequency_controller.py`
- **涉及文件**: `src/strategy/frequency_controller.py`, `tests/unit/test_frequency_controller.py`
- **验收标准**: 频率控制逻辑正确,禁止规则正确执行
- **预估工时**: 1小时
- **依赖关系**: 无

### 8.3 策略决策引擎
- [ ] 创建策略引擎模块 `src/strategy/strategy_engine.py`
- [ ] 实现 `StrategyEngine` 类
- [ ] 实现 `process_signal()` 方法,处理交易信号
- [ ] 实现开仓决策流程:检查频率→计算仓位→生成执行指令
- [ ] 实现平仓决策流程:计算平仓金额→生成执行指令
- [ ] 实现禁止项检查:禁止加仓,禁止杠杆,仅BTC/USDT
- [ ] 编写策略引擎单元测试 `tests/unit/test_strategy_engine.py`
- **涉及文件**: `src/strategy/strategy_engine.py`, `tests/unit/test_strategy_engine.py`
- **验收标准**: 策略决策流程正确,禁止项正确检查
- **预估工时**: 2小时
- **依赖关系**: 8.1, 8.2, 7.1

---

## 9. 订单状态机和异常恢复机制 (新增)

### 9.1 订单状态机
- [ ] 创建订单状态机模块 `src/execution/order_state_machine.py`
- [ ] 实现 `OrderStateMachine` 类
- [ ] 定义订单状态枚举 `OrderStatus`: PENDING, PARTIAL_FILLED, FILLED, REJECTED, CANCELLED
- [ ] 实现 `transition()` 方法,管理订单状态转换
  - PENDING → PARTIAL_FILLED (部分成交)
  - PENDING → FILLED (全部成交)
  - PARTIAL_FILLED → FILLED (剩余成交)
  - PENDING → REJECTED (被拒绝)
  - PENDING/PARTIAL_FILLED → CANCELLED (被撤销)
- [ ] 实现 `is_final_state()` 方法,判断是否达到最终状态
- [ ] 实现非法状态转换检测和异常抛出
- [ ] 编写单元测试 `tests/unit/test_order_state_machine.py`
- **涉及文件**: `src/execution/order_state_machine.py`, `tests/unit/test_order_state_machine.py`
- **技术要点**: 状态机设计、状态转换验证
- **验收标准**: 订单状态转换正确,非法转换被拦截
- **预估工时**: 2小时
- **依赖关系**: 无

### 9.2 挂单超时管理器
- [ ] 创建挂单超时管理模块 `src/execution/order_timeout_manager.py`
- [ ] 实现 `OrderTimeoutManager` 类
- [ ] 实现 `start_timer()` 方法,启动订单超时计时器
- [ ] 实现 `check_timeout()` 方法,检查订单是否超时
- [ ] 实现 `get_timeout_action()` 方法,获取超时处理动作
  - 限价单5分钟未成交 → "CANCEL_AND_MARKET" (撤单并改市价单)
  - 限价单30分钟未成交 → "FORCE_CANCEL" (强制撤单)
- [ ] 实现超时计时器管理(避免内存泄漏)
- [ ] 编写单元测试 `tests/unit/test_order_timeout_manager.py`
- **涉及文件**: `src/execution/order_timeout_manager.py`, `tests/unit/test_order_timeout_manager.py`
- **技术要点**: 计时器管理、超时检测
- **验收标准**: 超时检测准确,处理动作正确
- **预估工时**: 1.5小时
- **依赖关系**: 无

### 9.3 订单异常恢复器
- [ ] 创建订单异常恢复模块 `src/execution/order_recovery_handler.py`
- [ ] 实现 `OrderRecoveryHandler` 类
- [ ] 实现 `detect_anomaly()` 方法,检测订单异常
  - PARTIAL_FILL_TIMEOUT: 部分成交超时(30分钟无进展)
  - PENDING_TIMEOUT: 挂单超时无响应(60分钟)
  - REJECTED: 订单被拒绝
- [ ] 实现 `execute_recovery()` 方法,执行恢复策略
  - 部分成交超时 → 撤销剩余订单
  - 挂单无响应 → 主动查询交易所并同步状态
  - 订单被拒绝 → 记录拒绝原因并通知管理员
- [ ] 实现 `sync_order_status()` 方法,从交易所同步订单状态
- [ ] 编写单元测试 `tests/unit/test_order_recovery_handler.py`
- **涉及文件**: `src/execution/order_recovery_handler.py`, `tests/unit/test_order_recovery_handler.py`
- **技术要点**: 异常检测、恢复策略、状态同步
- **验收标准**: 异常检测准确,恢复策略正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 9.1, 9.2

---

## 10. 执行网关模块开发

### 10.1 订单管理器
- [ ] 创建执行网关模块 `src/execution/execution_gateway.py`
- [ ] 实现 `ExecutionGateway` 类
- [ ] 实现 `execute_open()` 方法,执行开仓操作
- [ ] 开仓流程:限价单(买一价)→5分钟未成交→撤单→市价单(滑点0.2%)
- [ ] 实现 `execute_close()` 方法,执行平仓操作
- [ ] 平仓流程:直接市价单(滑点0.2%)
- [ ] 实现 `poll_order_status()` 方法,轮询订单状态直到成交
- [ ] 集成订单状态机管理订单状态
- [ ] 集成挂单超时管理器
- [ ] 集成订单异常恢复器
- [ ] 实现订单超时处理(60秒未完成记录告警)
- [ ] 实现部分成交异常处理
- [ ] 编写执行网关单元测试 `tests/unit/test_execution_gateway.py`
- **涉及文件**: `src/execution/execution_gateway.py`, `tests/unit/test_execution_gateway.py`
- **技术要点**: 异步订单轮询,异常处理,重试机制,状态机集成
- **验收标准**: 订单正确执行,状态正确轮询,异常正确处理
- **预估工时**: 3.5小时
- **依赖关系**: 4.1, 9.1, 9.2, 9.3

### 10.2 交易结果处理器
- [ ] 创建结果处理模块 `src/execution/result_handler.py`
- [ ] 实现 `ResultHandler` 类
- [ ] 实现 `handle_execution_result()` 方法,处理交易结果
- [ ] 实现成交信息记录(价格、数量、手续费)
- [ ] 实现持仓状态更新
- [ ] 实现账户净值更新
- [ ] 实现滑点过大检测(>0.5%告警)
- [ ] 编写结果处理单元测试 `tests/unit/test_result_handler.py`
- **涉及文件**: `src/execution/result_handler.py`, `tests/unit/test_result_handler.py`
- **验收标准**: 交易结果正确处理并记录
- **预估工时**: 1.5小时
- **依赖关系**: 10.1

---

## 11. 风险控制模块开发

### 11.1 硬止损执行器
- [ ] 创建硬止损模块 `src/risk/stop_loss_executor.py`
- [ ] 实现 `StopLossExecutor` 类
- [ ] 实现 `check_stop_loss()` 方法,检查止损触发
- [ ] 实现 `execute_stop_loss()` 方法,执行止损平仓
- [ ] 实现止损价格更新逻辑(每4小时更新,只升不降)
- [ ] 编写硬止损单元测试 `tests/unit/test_stop_loss_executor.py`
- **涉及文件**: `src/risk/stop_loss_executor.py`, `tests/unit/test_stop_loss_executor.py`
- **验收标准**: 硬止损正确触发和执行
- **预估工时**: 1.5小时
- **依赖关系**: 10.1

### 11.2 闪崩保护器
- [ ] 创建闪崩保护模块 `src/risk/flash_crash_protector.py`
- [ ] 实现 `FlashCrashProtector` 类
- [ ] 实现 `monitor_flash_crash()` 方法,监控闪崩
- [ ] 闪崩条件:15分钟内下跌≥5%
- [ ] 实现 `execute_flash_crash_protection()` 方法,紧急平仓
- [ ] 编写闪崩保护单元测试 `tests/unit/test_flash_crash_protector.py`
- **涉及文件**: `src/risk/flash_crash_protector.py`, `tests/unit/test_flash_crash_protector.py`
- **验收标准**: 闪崩正确检测并触发保护
- **预估工时**: 1.5小时
- **依赖关系**: 4.1, 10.1

### 11.3 分级熔断恢复管理器 (新增)
- [ ] 创建分级熔断恢复模块 `src/risk/tiered_circuit_breaker.py`
- [ ] 实现 `TieredCircuitBreakerManager` 类
- [ ] 实现 `trigger_circuit_breaker()` 方法,触发熔断并记录到数据库
- [ ] 实现 `check_recovery_stage()` 方法,检查熔断恢复阶段
  - 熔断后第10天 → 允许恢复至50%仓位
  - 熔断后第20天 → 允许恢复至100%仓位
- [ ] 实现 `get_position_limit()` 方法,获取当前仓位限制比例
- [ ] 实现 `manual_recovery()` 方法,处理管理员提前恢复请求
- [ ] 实现 `auto_recovery_check()` 方法,自动恢复检查任务
- [ ] 实现熔断事件记录到 `circuit_breaker_events` 表
- [ ] 编写单元测试 `tests/unit/test_tiered_circuit_breaker.py`
- **涉及文件**: `src/risk/tiered_circuit_breaker.py`, `tests/unit/test_tiered_circuit_breaker.py`
- **技术要点**: 分级恢复逻辑、仓位限制、人工恢复处理
- **验收标准**: 分级恢复逻辑正确,仓位限制正确应用
- **预估工时**: 2.5小时
- **依赖关系**: 10.1

### 11.4 熔断管理器
- [ ] 创建熔断管理模块 `src/risk/circuit_breaker.py`
- [ ] 实现 `CircuitBreaker` 类
- [ ] 实现 `check_drawdown()` 方法,检查全局回撤
- [ ] 全局回撤熔断:回撤≥20%清仓并进入分级恢复期
- [ ] 实现黑天鹅熔断逻辑:5分钟跌幅≥3%平仓50%,24小时跌幅≥15%清仓并暂停7天
- [ ] 实现异常波动熔断:波动>10%且浮亏>8%强制平仓
- [ ] 实现熔断状态管理(暂停/恢复)
- [ ] 集成分级熔断恢复管理器
- [ ] 编写熔断管理单元测试 `tests/unit/test_circuit_breaker.py`
- **涉及文件**: `src/risk/circuit_breaker.py`, `tests/unit/test_circuit_breaker.py`
- **验收标准**: 熔断条件正确检测,熔断状态正确管理
- **预估工时**: 2.5小时
- **依赖关系**: 11.3

### 11.5 风险控制协调器
- [ ] 创建风控协调模块 `src/risk/risk_controller.py`
- [ ] 实现 `RiskController` 类,协调所有风控子模块
- [ ] 实现 `run_risk_check()` 方法,执行完整风控检查
- [ ] 实现风控优先级:风控指令优先于信号指令(一票否决权)
- [ ] 实现风控告警通知
- [ ] 编写风控协调单元测试 `tests/unit/test_risk_controller.py`
- **涉及文件**: `src/risk/risk_controller.py`, `tests/unit/test_risk_controller.py`
- **验收标准**: 风控流程正确执行,优先级正确
- **预估工时**: 2小时
- **依赖关系**: 11.1, 11.2, 11.4, 2.4

---

## 12. 监控指标体系模块 (新增)

### 12.1 数据新鲜度监控器
- [ ] 创建数据新鲜度监控模块 `src/monitor/data_freshness_monitor.py`
- [ ] 实现 `DataFreshnessMonitor` 类
- [ ] 实现 `check_all_data_sources()` 方法,检查所有数据源新鲜度
- [ ] 实现 `get_freshness_summary()` 方法,生成新鲜度统计摘要
- [ ] 实现 `check_stale_alert()` 方法,检查是否需要推送新鲜度告警(超24小时未更新)
- [ ] 实现新鲜度监控指标输出
- [ ] 编写单元测试 `tests/unit/test_data_freshness_monitor.py`
- **涉及文件**: `src/monitor/data_freshness_monitor.py`, `tests/unit/test_data_freshness_monitor.py`
- **技术要点**: 数据源监控、告警推送、指标统计
- **验收标准**: 数据新鲜度监控准确,告警正确触发
- **预估工时**: 1.5小时
- **依赖关系**: 1.1

### 12.2 策略性能监控器
- [ ] 创建策略性能监控模块 `src/monitor/strategy_performance_monitor.py`
- [ ] 实现 `StrategyPerformanceMonitor` 类
- [ ] 实现 `calculate_win_rate()` 方法,计算交易信号胜率(盈利交易次数/总交易次数)
- [ ] 实现 `calculate_profit_loss_ratio()` 方法,计算平均盈亏比(平均盈利金额/平均亏损金额)
- [ ] 实现 `calculate_max_consecutive_losses()` 方法,统计最长连续亏损次数
- [ ] 实现 `get_performance_summary()` 方法,生成性能统计摘要
- [ ] 实现性能指标持久化到 `monitoring_metrics` 表
- [ ] 编写单元测试 `tests/unit/test_strategy_performance_monitor.py`
- **涉及文件**: `src/monitor/strategy_performance_monitor.py`, `tests/unit/test_strategy_performance_monitor.py`
- **技术要点**: 统计计算、性能指标分析
- **验收标准**: 性能指标计算准确
- **预估工时**: 2小时
- **依赖关系**: 无

### 12.3 风控触发统计器
- [ ] 创建风控统计模块 `src/monitor/risk_stats_monitor.py`
- [ ] 实现 `RiskStatsMonitor` 类
- [ ] 实现 `record_circuit_breaker_trigger()` 方法,记录熔断触发事件
- [ ] 实现 `get_circuit_breaker_stats()` 方法,统计各类熔断累计触发次数
- [ ] 实现 `get_trigger_details()` 方法,获取熔断触发详情(类型、时间、原因)
- [ ] 实现风控统计指标持久化到 `monitoring_metrics` 表
- [ ] 编写单元测试 `tests/unit/test_risk_stats_monitor.py`
- **涉及文件**: `src/monitor/risk_stats_monitor.py`, `tests/unit/test_risk_stats_monitor.py`
- **技术要点**: 风控事件统计、详情记录
- **验收标准**: 风控统计准确,详情完整记录
- **预估工时**: 1.5小时
- **依赖关系**: 无

### 12.4 API调用统计器
- [ ] 创建API统计模块 `src/monitor/api_stats_monitor.py`
- [ ] 实现 `APIStatsMonitor` 类
- [ ] 实现 `record_api_call()` 方法,记录API调用(成功/失败、延迟)
- [ ] 实现 `calculate_success_rate()` 方法,计算API调用成功率
- [ ] 实现 `calculate_latency_distribution()` 方法,计算API延迟分布(P50、P95、P99)
- [ ] 实现 `get_api_stats()` 方法,获取API统计摘要
- [ ] 实现API统计指标持久化到 `monitoring_metrics` 表
- [ ] 编写单元测试 `tests/unit/test_api_stats_monitor.py`
- **涉及文件**: `src/monitor/api_stats_monitor.py`, `tests/unit/test_api_stats_monitor.py`
- **技术要点**: API监控、延迟统计、百分位计算
- **验收标准**: API统计准确,延迟分布计算正确
- **预估工时**: 2小时
- **依赖关系**: 无

### 12.5 监控指标汇总器
- [ ] 创建监控汇总模块 `src/monitor/metrics_aggregator.py`
- [ ] 实现 `MetricsAggregator` 类
- [ ] 实现 `aggregate_all_metrics()` 方法,汇总所有监控指标
- [ ] 实现 `export_metrics()` 方法,输出监控数据到文件
- [ ] 实现 `generate_daily_report()` 方法,生成每日状态报告
- [ ] 集成数据新鲜度、策略性能、风控统计、API统计监控器
- [ ] 编写单元测试 `tests/unit/test_metrics_aggregator.py`
- **涉及文件**: `src/monitor/metrics_aggregator.py`, `tests/unit/test_metrics_aggregator.py`
- **技术要点**: 指标汇总、报告生成
- **验收标准**: 监控指标正确汇总和输出
- **预估工时**: 2小时
- **依赖关系**: 12.1, 12.2, 12.3, 12.4

---

## 13. 监控告警模块开发

### 13.1 交易事件通知器
- [ ] 创建交易通知模块 `src/monitor/trade_notifier.py`
- [ ] 实现 `TradeNotifier` 类
- [ ] 实现 `notify_trade()` 方法,发送交易通知到Telegram
- [ ] 通知内容:交易类型、价格、数量、持仓变化、盈亏情况
- [ ] 实现敏感数据过滤(不包含余额、持仓大小)
- [ ] 编写交易通知单元测试 `tests/unit/test_trade_notifier.py`
- **涉及文件**: `src/monitor/trade_notifier.py`, `tests/unit/test_trade_notifier.py`
- **验收标准**: 交易通知正确发送,敏感数据已过滤
- **预估工时**: 1小时
- **依赖关系**: 4.5

### 13.2 告警管理器
- [ ] 创建告警管理模块 `src/monitor/alert_manager.py`
- [ ] 实现 `AlertManager` 类
- [ ] 实现 `send_data_alert()` 方法,发送数据异常告警
- [ ] 实现 `send_risk_alert()` 方法,发送风控告警
- [ ] 实现 `send_equity_alert()` 方法,发送净值回撤告警(单日回撤>5%)
- [ ] 实现 `send_freshness_alert()` 方法,发送数据新鲜度告警
- [ ] 实现告警频率控制(同类告警每5分钟一次)
- [ ] 编写告警管理单元测试 `tests/unit/test_alert_manager.py`
- **涉及文件**: `src/monitor/alert_manager.py`, `tests/unit/test_alert_manager.py`
- **验收标准**: 告警正确发送,频率控制正确
- **预估工时**: 1.5小时
- **依赖关系**: 4.5

### 13.3 监控数据输出器
- [ ] 创建监控输出模块 `src/monitor/metrics_exporter.py`
- [ ] 实现 `MetricsExporter` 类
- [ ] 实现 `export_metrics()` 方法,输出监控数据
- [ ] 监控数据:持仓状态、净值曲线、信号记录、风控指标
- [ ] 实现每日状态报告生成
- [ ] 实现监控数据写入本地文件(支持Grafana读取)
- [ ] 编写监控输出单元测试 `tests/unit/test_metrics_exporter.py`
- **涉及文件**: `src/monitor/metrics_exporter.py`, `tests/unit/test_metrics_exporter.py`
- **验收标准**: 监控数据正确输出
- **预估工时**: 1.5小时
- **依赖关系**: 12.5

---

## 14. 回测系统开发

### 14.1 历史数据加载器
- [ ] 创建回测数据模块 `src/backtest/data_loader.py`
- [ ] 实现 `BacktestDataLoader` 类
- [ ] 实现 `load_historical_data()` 方法,加载2019至今历史数据
- [ ] 实现训练期和测试期划分(2022-01-01为界)
- [ ] 实现数据缺失处理(使用前一日填充)
- [ ] 编写数据加载单元测试 `tests/unit/test_backtest_data_loader.py`
- **涉及文件**: `src/backtest/data_loader.py`, `tests/unit/test_backtest_data_loader.py`
- **验收标准**: 历史数据正确加载和划分
- **预估工时**: 1.5小时
- **依赖关系**: 无

### 14.2 回测模拟器
- [ ] 创建回测模拟模块 `src/backtest/backtest_engine.py`
- [ ] 实现 `BacktestEngine` 类
- [ ] 实现 `run_backtest()` 方法,执行回测
- [ ] 实现现实摩擦模拟:手续费0.1%、滑点0.1%、资金费率成本
- [ ] 实现链上数据延迟模拟(shift(2))
- [ ] 实现模拟账户管理
- [ ] 编写回测引擎单元测试 `tests/unit/test_backtest_engine.py`
- **涉及文件**: `src/backtest/backtest_engine.py`, `tests/unit/test_backtest_engine.py`
- **验收标准**: 回测正确执行,摩擦成本正确扣除
- **预估工时**: 3小时
- **依赖关系**: 14.1, 7.1, 8.3

### 14.3 回测评估指标计算器
- [ ] 创建回测评估模块 `src/backtest/metrics_calculator.py`
- [ ] 实现 `MetricsCalculator` 类
- [ ] 实现 `calculate_returns()` 方法,计算年化收益率
- [ ] 实现 `calculate_sharpe_ratio()` 方法,计算夏普比率
- [ ] 实现 `calculate_max_drawdown()` 方法,计算最大回撤
- [ ] 实现 `calculate_calmar_ratio()` 方法,计算卡尔玛比率
- [ ] 实现 `calculate_trade_stats()` 方法,计算胜率、盈亏比
- [ ] 实现 `calculate_excess_return()` 方法,计算超额收益
- [ ] 实现回测通过标准判断(年化收益≥BTC现货90%且最大回撤≤25%)
- [ ] 编写指标计算单元测试 `tests/unit/test_metrics_calculator.py`
- **涉及文件**: `src/backtest/metrics_calculator.py`, `tests/unit/test_metrics_calculator.py`
- **验收标准**: 所有评估指标计算正确
- **预估工时**: 2小时
- **依赖关系**: 14.2

### 14.4 极端行情回测器 (新增)
- [ ] 创建极端行情回测模块 `src/backtest/extreme_scenario_tester.py`
- [ ] 实现 `ExtremeScenarioTester` 类
- [ ] 实现 `test_black_swan()` 方法,测试黑天鹅场景(如2020年3月12日暴跌)
- [ ] 实现 `test_flash_crash()` 方法,测试闪崩场景
- [ ] 实现 `test_high_volatility()` 方法,测试高波动场景
- [ ] 实现 `verify_risk_control()` 方法,验证风控机制是否有效触发
- [ ] 实现 `check_max_loss()` 方法,检查极端行情下最大亏损是否超过50%
- [ ] 编写单元测试 `tests/unit/test_extreme_scenario_tester.py`
- **涉及文件**: `src/backtest/extreme_scenario_tester.py`, `tests/unit/test_extreme_scenario_tester.py`
- **技术要点**: 极端场景模拟、风控验证
- **验收标准**: 极端行情测试正确,风控验证准确
- **预估工时**: 2.5小时
- **依赖关系**: 14.2

### 14.5 参数敏感性分析器 (新增)
- [ ] 创建参数敏感性分析模块 `src/backtest/parameter_sensitivity_analyzer.py`
- [ ] 实现 `ParameterSensitivityAnalyzer` 类
- [ ] 实现 `analyze_single_parameter()` 方法,单参数变动分析(±20%变动测试)
- [ ] 实现 `analyze_multi_parameters()` 方法,多参数组合分析
- [ ] 实现 `calculate_sensitivity()` 方法,计算策略表现对参数变化的敏感度
- [ ] 实现 `check_robustness()` 方法,检查参数稳健性(收益变化>100%发出警告)
- [ ] 实现 `generate_sensitivity_report()` 方法,生成敏感性分析报告
- [ ] 编写单元测试 `tests/unit/test_parameter_sensitivity_analyzer.py`
- **涉及文件**: `src/backtest/parameter_sensitivity_analyzer.py`, `tests/unit/test_parameter_sensitivity_analyzer.py`
- **技术要点**: 参数变动测试、敏感度计算、稳健性分析
- **验收标准**: 参数敏感性分析正确,稳健性检查准确
- **预估工时**: 2.5小时
- **依赖关系**: 14.2

### 14.6 并发压力测试器 (新增)
- [ ] 创建并发压力测试模块 `src/backtest/concurrency_tester.py`
- [ ] 实现 `ConcurrencyTester` 类
- [ ] 实现 `test_concurrent_tasks()` 方法,模拟多个定时任务同时触发
- [ ] 实现 `monitor_resource_usage()` 方法,监控系统资源占用(内存、CPU)
- [ ] 实现 `check_task_failure_rate()` 方法,检查任务执行失败率
- [ ] 实现 `generate_concurrency_report()` 方法,生成并发测试报告
- [ ] 实现失败率>1%发出警告
- [ ] 编写单元测试 `tests/unit/test_concurrency_tester.py`
- **涉及文件**: `src/backtest/concurrency_tester.py`, `tests/unit/test_concurrency_tester.py`
- **技术要点**: 并发测试、资源监控、失败率统计
- **验收标准**: 并发测试正确,资源监控准确
- **预估工时**: 2小时
- **依赖关系**: 14.2

### 14.7 模拟盘验证器 (新增)
- [ ] 创建模拟盘验证模块 `src/backtest/paper_trading_validator.py`
- [ ] 实现 `PaperTradingValidator` 类
- [ ] 实现 `start_paper_trading()` 方法,在OKX Testnet环境启动模拟盘
- [ ] 实现 `monitor_environment_diff()` 方法,监控与真实交易环境的差异
- [ ] 实现 `check_performance()` 方法,检查模拟盘表现是否符合预期
- [ ] 实现 `validate_strategy()` 方法,验证策略在模拟盘的表现
- [ ] 实现连续运行30天验证通过判断
- [ ] 编写单元测试 `tests/unit/test_paper_trading_validator.py`
- **涉及文件**: `src/backtest/paper_trading_validator.py`, `tests/unit/test_paper_trading_validator.py`
- **技术要点**: Testnet集成、环境差异监控、长期验证
- **验收标准**: 模拟盘验证正确,环境差异监控准确
- **预估工时**: 3小时
- **依赖关系**: 4.1

### 14.8 回测报告生成器
- [ ] 创建回测报告模块 `src/backtest/report_generator.py`
- [ ] 实现 `ReportGenerator` 类
- [ ] 实现 `generate_report()` 方法,生成回测报告
- [ ] 报告内容:收益曲线、风险指标、交易统计、通过标准判断
- [ ] 实现报告导出为HTML或PDF
- [ ] 编写报告生成单元测试 `tests/unit/test_report_generator.py`
- **涉及文件**: `src/backtest/report_generator.py`, `tests/unit/test_report_generator.py`
- **验收标准**: 回测报告正确生成
- **预估工时**: 1.5小时
- **依赖关系**: 14.3, 14.4, 14.5, 14.6

---

## 15. 定时调度模块开发

### 15.1 定时任务调度器
- [ ] 创建调度模块 `src/scheduler/task_scheduler.py`
- [ ] 实现 `TaskScheduler` 类
- [ ] 实现每日数据采集任务:UTC 00:05
- [ ] 实现每日信号计算和交易执行任务:UTC 00:10
- [ ] 实现风控检查任务:每4小时
- [ ] 实现闪崩监控任务:每15分钟
- [ ] 实现止损价格更新任务:每4小时
- [ ] 实现数据新鲜度监控任务:每小时
- [ ] 实现监控指标统计任务:每5分钟
- [ ] 实现订单异常恢复检查任务:每10分钟
- [ ] 实现熔断分级恢复检查任务:每日UTC 00:30
- [ ] 实现错过执行处理(coalesce)
- [ ] 实现任务持久化
- [ ] 编写调度器单元测试 `tests/unit/test_task_scheduler.py`
- **涉及文件**: `src/scheduler/task_scheduler.py`, `tests/unit/test_task_scheduler.py`
- **技术要点**: APScheduler, CronTrigger
- **验收标准**: 所有定时任务正确调度执行
- **预估工时**: 2.5小时
- **依赖关系**: 3.6, 8.3, 11.5, 12.5

---

## 16. 主程序入口

### 16.1 主程序入口
- [ ] 创建主程序 `main.py`
- [ ] 实现系统初始化流程(配置加载、数据库初始化、日志初始化)
- [ ] 实现API权限验证
- [ ] 实现调度器启动
- [ ] 实现优雅退出处理(保存状态、关闭连接)
- [ ] 实现健康检查接口
- [ ] 编写主程序集成测试 `tests/integration/test_main.py`
- **涉及文件**: `main.py`, `tests/integration/test_main.py`
- **验收标准**: 系统正确启动和运行,优雅退出正常
- **预估工时**: 2小时
- **依赖关系**: 15.1

---

## 17. 单元测试补充

### 17.1 测试数据生成器
- [ ] 创建测试数据生成器 `tests/fixtures/data_generator.py`
- [ ] 实现模拟行情数据生成
- [ ] 实现模拟链上数据生成
- [ ] 实现模拟交易信号生成
- [ ] 实现模拟持仓数据生成
- [ ] 实现模拟熔断事件数据生成
- [ ] 实现模拟风控拦截数据生成
- **涉及文件**: `tests/fixtures/data_generator.py`
- **验收标准**: 测试数据生成正确
- **预估工时**: 1.5小时
- **依赖关系**: 无

### 17.2 Mock对象工厂
- [ ] 创建Mock工厂 `tests/fixtures/mock_factory.py`
- [ ] 实现OKX API Mock对象
- [ ] 实现Glassnode API Mock对象
- [ ] 实现Telegram API Mock对象
- [ ] 实现数据库Mock对象
- [ ] 实现风控模块Mock对象
- **涉及文件**: `tests/fixtures/mock_factory.py`
- **技术要点**: unittest.mock, pytest fixtures
- **验收标准**: Mock对象正确模拟外部依赖
- **预估工时**: 2小时
- **依赖关系**: 17.1

---

## 18. 集成测试开发

### 18.1 数据采集集成测试
- [ ] 创建数据采集集成测试 `tests/integration/test_data_collection_flow.py`
- [ ] 测试完整数据采集流程(OKX、链上、稳定币、情绪指数)
- [ ] 测试数据完整性校验
- [ ] 测试异常数据处理
- [ ] 测试数据持久化
- [ ] 测试数据时间戳和质量评分
- **涉及文件**: `tests/integration/test_data_collection_flow.py`
- **验收标准**: 数据采集流程正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 3.6, 17.2

### 18.2 信号计算集成测试
- [ ] 创建信号计算集成测试 `tests/integration/test_signal_calculation_flow.py`
- [ ] 测试完整信号计算流程(指标计算→体制识别→信号生成)
- [ ] 测试开仓信号生成
- [ ] 测试平仓信号生成
- [ ] 测试止损信号生成
- [ ] 测试风控拦截集成
- **涉及文件**: `tests/integration/test_signal_calculation_flow.py`
- **验收标准**: 信号计算流程正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 7.1, 2.4, 17.2

### 18.3 交易执行集成测试
- [ ] 创建交易执行集成测试 `tests/integration/test_trading_flow.py`
- [ ] 测试完整交易执行流程(信号→决策→执行→记录)
- [ ] 测试开仓流程
- [ ] 测试平仓流程
- [ ] 测试订单状态轮询和状态机
- [ ] 测试订单超时处理
- [ ] 测试订单异常恢复
- [ ] 测试风控拦截集成
- **涉及文件**: `tests/integration/test_trading_flow.py`
- **验收标准**: 交易执行流程正确执行
- **预估工时**: 3小时
- **依赖关系**: 10.1, 2.4, 17.2

### 18.4 风险控制集成测试
- [ ] 创建风控集成测试 `tests/integration/test_risk_control_flow.py`
- [ ] 测试完整风控流程
- [ ] 测试硬止损触发和执行
- [ ] 测试闪崩保护
- [ ] 测试熔断机制
- [ ] 测试分级熔断恢复
- [ ] 测试风控优先级
- [ ] 测试风控前置拦截
- **涉及文件**: `tests/integration/test_risk_control_flow.py`
- **验收标准**: 风控流程正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 11.5, 17.2

### 18.5 回测系统集成测试
- [ ] 创建回测集成测试 `tests/integration/test_backtest_flow.py`
- [ ] 测试完整回测流程
- [ ] 测试回测评估指标计算
- [ ] 测试极端行情回测
- [ ] 测试参数敏感性分析
- [ ] 测试并发压力测试
- [ ] 测试回测报告生成
- **涉及文件**: `tests/integration/test_backtest_flow.py`
- **验收标准**: 回测流程正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 14.8, 17.2

### 18.6 监控系统集成测试
- [ ] 创建监控集成测试 `tests/integration/test_monitoring_flow.py`
- [ ] 测试数据新鲜度监控
- [ ] 测试策略性能监控
- [ ] 测试风控触发统计
- [ ] 测试API调用统计
- [ ] 测试监控指标汇总和输出
- **涉及文件**: `tests/integration/test_monitoring_flow.py`
- **验收标准**: 监控流程正确执行
- **预估工时**: 2小时
- **依赖关系**: 12.5, 17.2

---

## 19. 部署配置开发

### 19.1 Docker配置
- [ ] 创建Dockerfile
- [ ] 配置Python 3.10基础镜像
- [ ] 安装系统依赖(gcc等)
- [ ] 安装Python依赖
- [ ] 创建数据目录和日志目录
- [ ] 配置环境变量
- [ ] 配置健康检查
- [ ] 配置启动命令
- **涉及文件**: `Dockerfile`
- **技术要点**: Docker多阶段构建,健康检查
- **验收标准**: Docker镜像正确构建和运行
- **预估工时**: 1.5小时
- **依赖关系**: 16.1

### 19.2 Docker Compose配置
- [ ] 创建docker-compose.yml
- [ ] 配置服务定义
- [ ] 配置环境变量注入
- [ ] 配置数据卷挂载(数据、日志、配置)
- [ ] 配置日志驱动和轮转
- [ ] 配置重启策略
- **涉及文件**: `docker-compose.yml`
- **验收标准**: Docker Compose正确编排服务
- **预估工时**: 1小时
- **依赖关系**: 19.1

### 19.3 部署脚本
- [ ] 创建部署脚本 `scripts/deploy.sh`
- [ ] 实现环境检查(Docker、Docker Compose)
- [ ] 实现配置文件检查
- [ ] 实现数据库初始化
- [ ] 实现服务启动
- [ ] 实现服务停止
- [ ] 实现服务重启
- [ ] 实现日志查看
- **涉及文件**: `scripts/deploy.sh`
- **验收标准**: 部署脚本正确执行
- **预估工时**: 1.5小时
- **依赖关系**: 19.2

### 19.4 运维脚本
- [ ] 创建数据库备份脚本 `scripts/backup_db.py`
- [ ] 创建日志清理脚本 `scripts/clean_logs.py`
- [ ] 创建配置更新脚本 `scripts/update_config.py`
- [ ] 创建健康检查脚本 `scripts/health_check.py`
- [ ] 创建手动平仓脚本 `scripts/manual_close.py`(紧急情况使用)
- [ ] 创建熔断恢复脚本 `scripts/manual_circuit_breaker_recovery.py`
- **涉及文件**: `scripts/backup_db.py`, `scripts/clean_logs.py`, `scripts/update_config.py`, `scripts/health_check.py`, `scripts/manual_close.py`, `scripts/manual_circuit_breaker_recovery.py`
- **验收标准**: 运维脚本正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 19.3

---

## 20. 文档完善

### 20.1 API文档
- [ ] 创建API文档 `docs/api.md`
- [ ] 文档化所有内部模块接口
- [ ] 文档化外部API调用方式
- [ ] 文档化数据模型定义
- [ ] 文档化风控拦截接口
- [ ] 文档化订单状态机接口
- **涉及文件**: `docs/api.md`
- **验收标准**: API文档完整清晰
- **预估工时**: 2.5小时
- **依赖关系**: 16.1

### 20.2 运维文档
- [ ] 创建运维文档 `docs/operations.md`
- [ ] 文档化部署流程
- [ ] 文档化配置说明
- [ ] 文档化监控指标
- [ ] 文档化常见问题处理
- [ ] 文档化告警处理流程
- [ ] 文档化熔断恢复流程
- **涉及文件**: `docs/operations.md`
- **验收标准**: 运维文档完整清晰
- **预估工时**: 2.5小时
- **依赖关系**: 19.4

### 20.3 回测使用文档
- [ ] 创建回测文档 `docs/backtest.md`
- [ ] 文档化回测执行方式
- [ ] 文档化回测参数配置
- [ ] 文档化回测报告解读
- [ ] 文档化策略参数调优建议
- [ ] 文档化极端行情测试方法
- [ ] 文档化参数敏感性分析方法
- **涉及文件**: `docs/backtest.md`
- **验收标准**: 回测文档完整清晰
- **预估工时**: 2小时
- **依赖关系**: 14.8

---

## 21. 最终验收测试

### 21.1 端到端测试
- [ ] 创建端到端测试 `tests/e2e/test_e2e.py`
- [ ] 测试完整系统运行流程
- [ ] 测试数据采集→信号计算→风控拦截→交易执行→风控→监控完整链路
- [ ] 测试定时任务调度
- [ ] 测试异常处理和告警
- [ ] 测试订单状态机和异常恢复
- [ ] 测试分级熔断恢复
- **涉及文件**: `tests/e2e/test_e2e.py`
- **验收标准**: 系统端到端运行正确
- **预估工时**: 3.5小时
- **依赖关系**: 18.6

### 21.2 性能测试
- [ ] 创建性能测试 `tests/performance/test_performance.py`
- [ ] 测试数据采集性能(5分钟内完成)
- [ ] 测试信号计算性能(30秒内完成)
- [ ] 测试订单执行性能(10秒内完成)
- [ ] 测试内存占用(≤2GB)
- [ ] 测试CPU使用率(≤50%)
- [ ] 测试并发处理能力
- **涉及文件**: `tests/performance/test_performance.py`
- **验收标准**: 所有性能指标达标
- **预估工时**: 2.5小时
- **依赖关系**: 21.1

### 21.3 安全测试
- [ ] 创建安全测试 `tests/security/test_security.py`
- [ ] 测试API密钥脱敏
- [ ] 测试敏感数据过滤
- [ ] 测试权限控制
- [ ] 测试审计日志记录
- [ ] 测试风控拦截安全性
- **涉及文件**: `tests/security/test_security.py`
- **验收标准**: 所有安全要求达标
- **预估工时**: 2小时
- **依赖关系**: 21.1

---

## 任务统计汇总

**总任务数**: 141个任务  
**预估总工时**: 约148.5小时(约19个工作日)

**任务分组统计**:
- 数据时间戳管理和质量评分模块(新增): 3个任务, 5.5小时
- 风控前置拦截模块(新增): 4个任务, 7小时
- 数据采集模块开发: 6个任务, 8小时
- 外部API接口封装层: 5个任务, 8.5小时
- 指标计算模块开发: 2个任务, 3.5小时
- 体制识别模块开发: 1个任务, 1.5小时
- 信号生成模块开发: 1个任务, 2.5小时
- 策略决策引擎开发: 3个任务, 5小时
- 订单状态机和异常恢复机制(新增): 3个任务, 6小时
- 执行网关模块开发: 2个任务, 5小时
- 风险控制模块开发: 5个任务, 10小时
- 监控指标体系模块(新增): 5个任务, 9小时
- 监控告警模块开发: 3个任务, 4小时
- 回测系统开发: 8个任务, 19小时
- 定时调度模块开发: 1个任务, 2.5小时
- 主程序入口: 1个任务, 2小时
- 单元测试补充: 2个任务, 3.5小时
- 集成测试开发: 6个任务, 14.5小时
- 部署配置开发: 4个任务, 6.5小时
- 文档完善: 3个任务, 7小时
- 最终验收测试: 3个任务, 8小时

**新增模块统计**:
1. 数据时间戳管理和质量评分模块: 3个任务, 5.5小时
2. 风控前置拦截模块: 4个任务, 7小时
3. 订单状态机和异常恢复机制: 3个任务, 6小时
4. 分级熔断恢复机制: 1个任务(包含在风险控制模块中)
5. 完整监控指标体系: 5个任务, 9小时
6. 加强的测试策略(极端行情、参数敏感性、并发压力、模拟盘): 4个任务, 10小时

**关键路径**:
1. 数据时间戳管理 → 数据质量评分 → 数据采集
2. 风控前置拦截 → 策略引擎 → 执行网关
3. 订单状态机 → 执行网关 → 订单异常恢复
4. 分级熔断恢复 → 风控协调器
5. 监控指标体系 → 调度器 → 主程序

**优先级排序**:
- P0(必须): 1-16章节(核心功能,包括新增模块)
- P1(重要): 17-18章节(测试)
- P2(必要): 19章节(部署)
- P3(建议): 20-21章节(文档和验收)

**注意事项**:
1. 项目基础设施已实现(目录结构、配置、日志、数据模型、调度器),无需重复开发
2. 新增模块与现有模块需要良好集成
3. 所有新功能需编写单元测试和集成测试
4. 回测系统增强功能(极端行情、参数敏感性、并发压力、模拟盘)需要充分测试

---

**文档结束**
