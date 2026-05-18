# AOSFT-MVP 编码任务规划

**版本**: v1.0  
**项目名称**: AOSFT-MVP — 链上与体制感知的BTC趋势跟踪系统  
**生成日期**: 2026-05-18

---

## 1. 项目基础设施搭建

### 1.1 项目目录结构初始化
- [ ] 创建项目根目录结构：`src/`, `tests/`, `config/`, `data/`, `logs/`, `scripts/`
- [ ] 创建源代码子目录：`src/collectors/`, `src/indicators/`, `src/regime/`, `src/signals/`, `src/strategy/`, `src/execution/`, `src/risk/`, `src/monitor/`, `src/backtest/`, `src/scheduler/`, `src/models/`, `src/utils/`
- [ ] 创建测试子目录：`tests/unit/`, `tests/integration/`, `tests/fixtures/`
- [ ] 创建配置文件目录：`config/`
- **涉及文件**: 项目根目录结构
- **验收标准**: 所有目录创建成功，符合分层架构设计
- **预估工时**: 0.5小时
- **依赖关系**: 无

### 1.2 依赖管理和环境配置
- [ ] 创建`requirements.txt`文件，添加核心依赖：ccxt>=4.0.0, pandas>=2.0.0, numpy>=1.24.0, apscheduler>=3.10.0, requests>=2.31.0, python-telegram-bot>=20.0, pydantic>=2.0.0, python-dotenv>=1.0.0
- [ ] 创建`.env.example`模板文件，包含所有环境变量配置项（OKX_API_KEY, OKX_SECRET, OKX_PASSWORD, GLASSNODE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID）
- [ ] 创建`.gitignore`文件，排除敏感文件（.env, data/*.db, logs/*.log, __pycache__/）
- [ ] 创建`README.md`项目说明文档
- **涉及文件**: `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- **验收标准**: 所有依赖文件创建完成，环境变量模板包含必要配置项
- **预估工时**: 1小时
- **依赖关系**: 1.1

### 1.3 数据库初始化脚本
- [ ] 创建数据库初始化脚本`scripts/init_db.py`，创建所有表结构
- [ ] 实现`daily_ohlcv`表创建逻辑（包含字段约束和索引）
- [ ] 实现`onchain_netflow`表创建逻辑
- [ ] 实现`stablecoin_supply`表创建逻辑
- [ ] 实现`fear_greed_index`表创建逻辑
- [ ] 实现`trade_signals`表创建逻辑
- [ ] 实现`positions`表创建逻辑
- [ ] 实现`account_equity`表创建逻辑
- [ ] 实现`system_config`表创建逻辑并插入默认配置值
- [ ] 编写数据库初始化单元测试`tests/unit/test_db_init.py`
- **涉及文件**: `scripts/init_db.py`, `tests/unit/test_db_init.py`
- **技术要点**: SQLite3数据库，字段约束CHECK，索引创建，默认配置初始化
- **验收标准**: 数据库初始化成功，所有表结构正确创建，默认配置写入成功
- **预估工时**: 2小时
- **依赖关系**: 1.2

### 1.4 配置管理模块
- [ ] 创建配置管理模块`src/utils/config.py`
- [ ] 实现配置加载功能，从环境变量和配置文件读取配置
- [ ] 实现API密钥脱敏功能`mask_api_key()`
- [ ] 实现配置验证功能，确保必填配置项存在
- [ ] 创建系统配置参数数据类`SystemConfig`（使用Pydantic）
- [ ] 编写配置管理单元测试`tests/unit/test_config.py`
- **涉及文件**: `src/utils/config.py`, `tests/unit/test_config.py`
- **技术要点**: Pydantic数据验证，环境变量读取，配置脱敏
- **验收标准**: 配置加载成功，必填项验证通过，敏感信息正确脱敏
- **预估工时**: 1.5小时
- **依赖关系**: 1.2

### 1.5 日志系统初始化
- [ ] 创建日志配置模块`src/utils/logger.py`
- [ ] 实现日志轮转机制（保留最近90天日志）
- [ ] 实现安全日志格式化器`SecureFormatter`，自动脱敏敏感信息
- [ ] 配置不同级别日志输出（DEBUG, INFO, WARNING, ERROR）
- [ ] 创建审计日志记录器`AuditLogger`类
- **涉及文件**: `src/utils/logger.py`
- **技术要点**: logging模块，日志轮转，正则表达式脱敏
- **验收标准**: 日志系统正常工作，敏感信息自动脱敏，日志文件按日期轮转
- **预估工时**: 1.5小时
- **依赖关系**: 1.4

### 1.6 Git仓库初始化
- [ ] 初始化Git仓库（如尚未初始化）`git init`
- [ ] 创建`.gitignore`文件，排除敏感文件和临时文件
  - 排除`.env`、`*.db`、`*.log`、`__pycache__/`、`.pytest_cache/`、`*.pyc`
  - 排除虚拟环境目录`venv/`、`.venv/`
  - 排除IDE配置文件`.vscode/`、`.idea/`
- [ ] 配置Git用户信息`git config user.name`和`git config user.email`
- [ ] 创建初始提交`git commit -m "chore: 项目初始化"`
- [ ] 创建分支结构
  - 创建develop分支`git checkout -b develop`
  - 推送master和develop分支到远程仓库
- [ ] 创建分支保护规则（在GitHub/GitLab配置）
  - master分支禁止直接推送，必须通过PR合并
  - develop分支禁止直接推送，必须通过PR合并
- [ ] 编写CONTRIBUTING.md贡献指南文档
  - 说明分支管理策略（Git Flow）
  - 说明提交信息规范（Conventional Commits）
  - 说明PR创建和代码审查流程
- **涉及文件**: `.gitignore`, `CONTRIBUTING.md`
- **技术要点**: Git Flow工作流，分支保护，Conventional Commits规范
- **验收标准**: 
  - Git仓库初始化成功，分支结构正确
  - `.gitignore`正确排除敏感文件
  - CONTRIBUTING.md文档完整清晰
  - 分支保护规则配置完成
- **预估工时**: 1小时
- **依赖关系**: 1.2

---

## 2. 数据模型层开发

### 2.1 核心枚举和数据类定义
- [ ] 创建数据模型文件`src/models/enums.py`
- [ ] 定义`MarketRegime`枚举（BULL_VOLATILE, BEAR_VOLATILE, LOW_VOLATILE）
- [ ] 定义`SignalType`枚举（OPEN, CLOSE, STOP_LOSS, FORCED_CLOSE）
- [ ] 定义`PositionStatus`枚举（OPEN, CLOSED）
- [ ] 定义`DataSource`枚举（GLASSNODE, CRYPTOQUANT）
- **涉及文件**: `src/models/enums.py`
- **技术要点**: Python Enum类
- **验收标准**: 所有枚举定义正确，值符合需求规格
- **预估工时**: 0.5小时
- **依赖关系**: 1.5

### 2.2 Pydantic数据模型定义
- [ ] 创建数据模型文件`src/models/schemas.py`
- [ ] 实现`OHLCV`数据模型，包含价格验证逻辑（high>=open/close, low<=open/close）
- [ ] 实现`OnchainNetflow`数据模型
- [ ] 实现`StablecoinSupply`数据模型
- [ ] 实现`FearGreedIndex`数据模型
- [ ] 实现`TradeSignal`数据模型
- [ ] 实现`Position`数据模型，包含止损价验证逻辑
- [ ] 实现`AccountEquity`数据模型，包含净值计算验证
- [ ] 编写数据模型单元测试`tests/unit/test_schemas.py`
- **涉及文件**: `src/models/schemas.py`, `tests/unit/test_schemas.py`
- **技术要点**: Pydantic BaseModel, Field验证器, @validator装饰器
- **验收标准**: 所有数据模型验证逻辑正确，非法数据抛出验证错误
- **预估工时**: 2小时
- **依赖关系**: 2.1

---

## 3. 数据仓库层开发

### 3.1 数据仓库基础类
- [ ] 创建数据仓库模块`src/models/repository.py`
- [ ] 实现`DataRepository`类，封装SQLite数据库连接
- [ ] 实现数据库连接池管理
- [ ] 实现通用CRUD操作方法
- [ ] 实现数据库异常处理和重试机制
- **涉及文件**: `src/models/repository.py`
- **技术要点**: SQLite3连接管理，上下文管理器，异常处理
- **验收标准**: 数据库连接正常，CRUD操作正确执行
- **预估工时**: 1.5小时
- **依赖关系**: 2.2

### 3.2 日线行情数据访问层
- [ ] 实现`save_ohlcv()`方法，保存日线数据到`daily_ohlcv`表
- [ ] 实现`load_ohlcv()`方法，支持按日期范围查询历史数据
- [ ] 实现`get_latest_ohlcv()`方法，获取最近一日数据
- [ ] 实现数据去重逻辑（UNIQUE约束处理）
- [ ] 编写日线数据访问单元测试`tests/unit/test_ohlcv_repository.py`
- **涉及文件**: `src/models/repository.py`, `tests/unit/test_ohlcv_repository.py`
- **验收标准**: 日线数据正确保存和查询，去重逻辑正确
- **预估工时**: 1.5小时
- **依赖关系**: 3.1

### 3.3 链上数据访问层
- [ ] 实现`save_netflow()`方法，保存净流入数据
- [ ] 实现`load_netflow()`方法，支持查询最近N天数据
- [ ] 实现`save_stablecoin_supply()`方法，保存稳定币供应数据
- [ ] 实现`load_stablecoin_supply()`方法，查询稳定币数据
- [ ] 实现数据延迟标记处理
- [ ] 编写链上数据访问单元测试`tests/unit/test_onchain_repository.py`
- **涉及文件**: `src/models/repository.py`, `tests/unit/test_onchain_repository.py`
- **验收标准**: 链上数据正确保存和查询，延迟标记正确处理
- **预估工时**: 1.5小时
- **依赖关系**: 3.1

### 3.4 交易信号和持仓数据访问层
- [ ] 实现`save_signal()`方法，保存交易信号记录
- [ ] 实现`load_signals()`方法，查询历史信号
- [ ] 实现`save_position()`方法，保存持仓记录
- [ ] 实现`load_current_position()`方法，查询当前持仓（status='OPEN'）
- [ ] 实现`update_position()`方法，更新持仓状态
- [ ] 编写交易数据访问单元测试`tests/unit/test_trade_repository.py`
- **涉及文件**: `src/models/repository.py`, `tests/unit/test_trade_repository.py`
- **验收标准**: 交易信号和持仓数据正确保存和查询
- **预估工时**: 1.5小时
- **依赖关系**: 3.1

### 3.5 账户净值数据访问层
- [ ] 实现`save_equity()`方法，保存账户净值记录
- [ ] 实现`load_equity()`方法，查询历史净值
- [ ] 实现`get_latest_equity()`方法，获取最近净值记录
- [ ] 实现最大回撤和历史最高净值计算逻辑
- [ ] 编写净值数据访问单元测试`tests/unit/test_equity_repository.py`
- **涉及文件**: `src/models/repository.py`, `tests/unit/test_equity_repository.py`
- **验收标准**: 账户净值正确保存和查询，回撤计算正确
- **预估工时**: 1小时
- **依赖关系**: 3.1

---

## 4. 外部API接口封装层

### 4.1 OKX交易所接口封装
- [ ] 创建OKX接口模块`src/collectors/okx_interface.py`
- [ ] 实现`OKXMarketInterface`类，封装行情数据查询接口
- [ ] 实现`fetch_ohlcv()`方法，获取日线K线数据（返回Pandas DataFrame）
- [ ] 实现`fetch_ticker()`方法，获取最新价格信息
- [ ] 实现`OKXTradingInterface`类，封装交易执行接口
- [ ] 实现`create_limit_order()`方法，创建限价单
- [ ] 实现`create_market_order()`方法，创建市价单，支持滑点容忍设置
- [ ] 实现`cancel_order()`方法，撤销订单
- [ ] 实现`fetch_order()`方法，查询订单状态
- [ ] 实现`fetch_balance()`方法，查询账户余额
- [ ] 实现`fetch_positions()`方法，查询持仓信息（永续合约）
- [ ] 实现`fetch_funding_rate()`方法，查询资金费率（永续合约）
- [ ] 实现API调用重试和超时机制
- [ ] 编写OKX接口单元测试`tests/unit/test_okx_interface.py`
- **涉及文件**: `src/collectors/okx_interface.py`, `tests/unit/test_okx_interface.py`
- **技术要点**: CCXT库，异常处理，重试机制，DataFrame转换
- **验收标准**: OKX API调用成功，数据格式正确，异常情况正确处理
- **预估工时**: 3小时
- **依赖关系**: 3.2

### 4.2 链上数据接口封装
- [ ] 创建链上接口模块`src/collectors/onchain_interface.py`
- [ ] 实现`GlassnodeInterface`类
- [ ] 实现`get_exchange_netflow()`方法，获取交易所BTC净流入数据
- [ ] 实现`CryptoQuantInterface`类（备选数据源）
- [ ] 实现数据延迟shift(2)处理，确保不使用未来信息
- [ ] 实现API调用重试和异常处理
- [ ] 编写链上接口单元测试`tests/unit/test_onchain_interface.py`
- **涉及文件**: `src/collectors/onchain_interface.py`, `tests/unit/test_onchain_interface.py`
- **技术要点**: Requests库，API认证，数据延迟处理
- **验收标准**: 链上数据获取成功，数据延迟正确应用
- **预估工时**: 2小时
- **依赖关系**: 3.3

### 4.3 稳定币数据接口封装
- [ ] 创建稳定币接口模块`src/collectors/stablecoin_interface.py`
- [ ] 实现`CoinGeckoInterface`类
- [ ] 实现`get_stablecoin_supply()`方法，获取USDT和USDC供应量
- [ ] 实现7日变化率计算逻辑
- [ ] 编写稳定币接口单元测试`tests/unit/test_stablecoin_interface.py`
- **涉及文件**: `src/collectors/stablecoin_interface.py`, `tests/unit/test_stablecoin_interface.py`
- **验收标准**: 稳定币数据获取成功，变化率计算正确
- **预估工时**: 1小时
- **依赖关系**: 3.3

### 4.4 情绪指数接口封装
- [ ] 创建情绪指数接口模块`src/collectors/sentiment_interface.py`
- [ ] 实现`FearGreedIndexInterface`类
- [ ] 实现`get_index()`方法，获取Crypto Fear & Greed Index
- [ ] 实现分类标签映射逻辑（Extreme Fear, Fear, Neutral, Greed, Extreme Greed）
- [ ] 编写情绪指数接口单元测试`tests/unit/test_sentiment_interface.py`
- **涉及文件**: `src/collectors/sentiment_interface.py`, `tests/unit/test_sentiment_interface.py`
- **验收标准**: 情绪指数获取成功，分类标签正确映射
- **预估工时**: 1小时
- **依赖关系**: 3.3

### 4.5 Telegram通知接口封装
- [ ] 创建Telegram接口模块`src/monitor/telegram_interface.py`
- [ ] 实现`TelegramInterface`类
- [ ] 实现`send_trade_notification()`方法，发送交易通知
- [ ] 实现`send_alert()`方法，发送告警消息
- [ ] 实现敏感数据过滤功能`filter_sensitive_data()`
- [ ] 实现推送失败处理（不影响主流程）
- [ ] 编写Telegram接口单元测试`tests/unit/test_telegram_interface.py`
- **涉及文件**: `src/monitor/telegram_interface.py`, `tests/unit/test_telegram_interface.py`
- **技术要点**: python-telegram-bot库，异步消息发送
- **验收标准**: Telegram消息成功发送，敏感数据已过滤
- **预估工时**: 1.5小时
- **依赖关系**: 3.4

---

## 5. 数据采集模块开发

### 5.1 数据采集器基类
- [ ] 创建数据采集器基类`src/collectors/base_collector.py`
- [ ] 实现`BaseCollector`抽象类
- [ ] 定义数据采集标准接口`collect()`方法
- [ ] 实现数据校验逻辑`validate_data()`方法
- [ ] 实现数据存储逻辑`save_to_db()`方法
- [ ] 实现异常处理和告警逻辑
- **涉及文件**: `src/collectors/base_collector.py`
- **验收标准**: 基类定义完整，子类可继承使用
- **预估工时**: 1小时
- **依赖关系**: 4.4

### 5.2 OKX行情数据采集器
- [ ] 创建OKX采集器`src/collectors/ohlcv_collector.py`
- [ ] 实现`OHLCVCollector`类，继承`BaseCollector`
- [ ] 实现`collect()`方法，调用OKX API获取日线数据
- [ ] 实现数据完整性校验（价格>0，交易量>0）
- [ ] 实现异常数据处理（使用前一日数据）
- [ ] 编写OKX采集器单元测试`tests/unit/test_ohlcv_collector.py`
- **涉及文件**: `src/collectors/ohlcv_collector.py`, `tests/unit/test_ohlcv_collector.py`
- **验收标准**: 日线数据正确采集并保存，异常数据正确处理
- **预估工时**: 1.5小时
- **依赖关系**: 5.1, 4.1

### 5.3 链上数据采集器
- [ ] 创建链上采集器`src/collectors/netflow_collector.py`
- [ ] 实现`NetflowCollector`类
- [ ] 实现从Glassnode/CryptoQuant获取净流入数据
- [ ] 实现数据延迟处理（shift(2)）
- [ ] 实现数据源降级处理（主数据源失败时使用备用源）
- [ ] 编写链上采集器单元测试`tests/unit/test_netflow_collector.py`
- **涉及文件**: `src/collectors/netflow_collector.py`, `tests/unit/test_netflow_collector.py`
- **验收标准**: 链上数据正确采集，延迟处理正确
- **预估工时**: 1.5小时
- **依赖关系**: 5.1, 4.2

### 5.4 稳定币数据采集器
- [ ] 创建稳定币采集器`src/collectors/stablecoin_collector.py`
- [ ] 实现`StablecoinCollector`类
- [ ] 实现从CoinGecko获取稳定币供应数据
- [ ] 实现7日变化量计算
- [ ] 编写稳定币采集器单元测试`tests/unit/test_stablecoin_collector.py`
- **涉及文件**: `src/collectors/stablecoin_collector.py`, `tests/unit/test_stablecoin_collector.py`
- **验收标准**: 稳定币数据正确采集，变化量计算正确
- **预估工时**: 1小时
- **依赖关系**: 5.1, 4.3

### 5.5 情绪指数采集器
- [ ] 创建情绪指数采集器`src/collectors/sentiment_collector.py`
- [ ] 实现`SentimentCollector`类
- [ ] 实现从alternative.me获取情绪指数
- [ ] 编写情绪指数采集器单元测试`tests/unit/test_sentiment_collector.py`
- **涉及文件**: `src/collectors/sentiment_collector.py`, `tests/unit/test_sentiment_collector.py`
- **验收标准**: 情绪指数正确采集并保存
- **预估工时**: 1小时
- **依赖关系**: 5.1, 4.4

### 5.6 数据采集协调器
- [ ] 创建数据采集协调器`src/collectors/data_collector.py`
- [ ] 实现`DataCollector`类，协调所有采集器
- [ ] 实现`run_daily_collection()`方法，执行每日数据采集流程
- [ ] 实现数据完整性校验，检查所有数据源是否采集成功
- [ ] 实现采集失败告警通知
- [ ] 实现采集性能监控（5分钟内完成）
- [ ] 编写协调器单元测试`tests/unit/test_data_collector.py`
- **涉及文件**: `src/collectors/data_collector.py`, `tests/unit/test_data_collector.py`
- **验收标准**: 所有数据源正确采集，异常情况正确处理和告警
- **预估工时**: 2小时
- **依赖关系**: 5.2, 5.3, 5.4, 5.5

---

## 6. 指标计算模块开发

### 6.1 技术指标计算器
- [ ] 创建指标计算模块`src/indicators/technical_indicators.py`
- [ ] 实现`TechnicalIndicators`类
- [ ] 实现`calculate_ma()`方法，计算移动平均线MA(20)
- [ ] 实现`calculate_atr()`方法，计算平均真实波动幅度ATR(14)
- [ ] 实现`calculate_atr_ma()`方法，计算ATR的30日移动平均值
- [ ] 实现边界条件处理（历史数据不足情况）
- [ ] 编写技术指标计算单元测试`tests/unit/test_technical_indicators.py`
- **涉及文件**: `src/indicators/technical_indicators.py`, `tests/unit/test_technical_indicators.py`
- **技术要点**: Pandas滚动计算，NumPy数组运算
- **验收标准**: 技术指标计算正确，与标准公式一致
- **预估工时**: 2小时
- **依赖关系**: 3.2

### 6.2 链上指标计算器
- [ ] 创建链上指标模块`src/indicators/onchain_indicators.py`
- [ ] 实现`OnchainIndicators`类
- [ ] 实现`calculate_netflow_trend()`方法，计算净流入7日均值
- [ ] 实现`calculate_stablecoin_change()`方法，计算稳定币7日变化量
- [ ] 实现连续信号检测逻辑（连续3日满足条件）
- [ ] 编写链上指标计算单元测试`tests/unit/test_onchain_indicators.py`
- **涉及文件**: `src/indicators/onchain_indicators.py`, `tests/unit/test_onchain_indicators.py`
- **验收标准**: 链上指标计算正确，连续信号检测正确
- **预估工时**: 1.5小时
- **依赖关系**: 3.3

---

## 7. 体制识别模块开发

### 7.1 市场体制识别器
- [ ] 创建体制识别模块`src/regime/regime_detector.py`
- [ ] 实现`RegimeDetector`类
- [ ] 实现`detect_regime()`方法，根据技术指标判断市场体制
- [ ] 实现BULL_VOLATILE判定逻辑：收盘价>MA(20)且ATR(14)>ATR均线
- [ ] 实现BEAR_VOLATILE判定逻辑：收盘价≤MA(20)且ATR(14)>ATR均线
- [ ] 实现LOW_VOLATILE判定逻辑：ATR(14)≤ATR均线
- [ ] 编写体制识别单元测试`tests/unit/test_regime_detector.py`
- **涉及文件**: `src/regime/regime_detector.py`, `tests/unit/test_regime_detector.py`
- **验收标准**: 市场体制识别正确，符合需求规则定义
- **预估工时**: 1.5小时
- **依赖关系**: 6.1

---

## 8. 信号生成模块开发

### 8.1 信号生成器
- [ ] 创建信号生成模块`src/signals/signal_generator.py`
- [ ] 实现`SignalGenerator`类
- [ ] 实现`generate_open_signal()`方法，检查开仓条件
- [ ] 开仓条件：体制BULL_VOLATILE，净流入均值<0，稳定币变化>0，情绪指数<80
- [ ] 实现`generate_close_signal()`方法，检查平仓条件
- [ ] 平仓条件1：体制转为BEAR_VOLATILE
- [ ] 平仓条件2：净流入均值连续3日>0
- [ ] 平仓条件3：稳定币变化连续3日<0
- [ ] 实现`generate_stop_loss_signal()`方法，检查硬止损触发
- [ ] 硬止损条件：当前价格≤入场价-2×ATR(14)
- [ ] 实现`generate_signals()`方法，综合生成所有信号
- [ ] 编写信号生成单元测试`tests/unit/test_signal_generator.py`
- **涉及文件**: `src/signals/signal_generator.py`, `tests/unit/test_signal_generator.py`
- **验收标准**: 信号生成逻辑正确，所有条件正确检查
- **预估工时**: 2.5小时
- **依赖关系**: 7.1, 6.2

---

## 9. 策略决策引擎开发

### 9.1 仓位管理器
- [ ] 创建仓位管理模块`src/strategy/position_manager.py`
- [ ] 实现`PositionManager`类
- [ ] 实现`calculate_position_size()`方法，计算开仓金额
- [ ] 仓位计算：账户净值×50%，风险控制止损亏损≤5%
- [ ] 实现`calculate_stop_loss()`方法，计算止损价格
- [ ] 止损价=入场价-2×ATR(14)，止损价只升不降
- [ ] 实现`update_stop_loss()`方法，每4小时更新止损价
- [ ] 编写仓位管理单元测试`tests/unit/test_position_manager.py`
- **涉及文件**: `src/strategy/position_manager.py`, `tests/unit/test_position_manager.py`
- **验收标准**: 仓位计算正确，止损价格计算正确
- **预估工时**: 2小时
- **依赖关系**: 3.4, 6.1

### 9.2 交易频率控制器
- [ ] 创建频率控制模块`src/strategy/frequency_controller.py`
- [ ] 实现`FrequencyController`类
- [ ] 实现已持仓禁止新开仓逻辑
- [ ] 实现平仓后至少1日才能开仓逻辑
- [ ] 实现合约模式资金费率检查（资金费率<-0.1%暂不开仓）
- [ ] 编写频率控制单元测试`tests/unit/test_frequency_controller.py`
- **涉及文件**: `src/strategy/frequency_controller.py`, `tests/unit/test_frequency_controller.py`
- **验收标准**: 频率控制逻辑正确，禁止规则正确执行
- **预估工时**: 1小时
- **依赖关系**: 3.4

### 9.3 策略决策引擎
- [ ] 创建策略引擎模块`src/strategy/strategy_engine.py`
- [ ] 实现`StrategyEngine`类
- [ ] 实现`process_signal()`方法，处理交易信号
- [ ] 实现开仓决策流程：检查频率→计算仓位→生成执行指令
- [ ] 实现平仓决策流程：计算平仓金额→生成执行指令
- [ ] 实现禁止项检查：禁止加仓，禁止杠杆，仅BTC/USDT
- [ ] 编写策略引擎单元测试`tests/unit/test_strategy_engine.py`
- **涉及文件**: `src/strategy/strategy_engine.py`, `tests/unit/test_strategy_engine.py`
- **验收标准**: 策略决策流程正确，禁止项正确检查
- **预估工时**: 2小时
- **依赖关系**: 9.1, 9.2, 8.1

---

## 10. 执行网关模块开发

### 10.1 订单管理器
- [ ] 创建执行网关模块`src/execution/execution_gateway.py`
- [ ] 实现`ExecutionGateway`类
- [ ] 实现`execute_open()`方法，执行开仓操作
- [ ] 开仓流程：限价单（买一价）→5分钟未成交→撤单→市价单（滑点0.2%）
- [ ] 实现`execute_close()`方法，执行平仓操作
- [ ] 平仓流程：直接市价单（滑点0.2%）
- [ ] 实现`poll_order_status()`方法，轮询订单状态直到成交
- [ ] 实现订单超时处理（60秒未完成记录告警）
- [ ] 实现部分成交异常处理
- [ ] 编写执行网关单元测试`tests/unit/test_execution_gateway.py`
- **涉及文件**: `src/execution/execution_gateway.py`, `tests/unit/test_execution_gateway.py`
- **技术要点**: 异步订单轮询，异常处理，重试机制
- **验收标准**: 订单正确执行，状态正确轮询，异常正确处理
- **预估工时**: 3小时
- **依赖关系**: 4.1, 3.4

### 10.2 交易结果处理器
- [ ] 创建结果处理模块`src/execution/result_handler.py`
- [ ] 实现`ResultHandler`类
- [ ] 实现`handle_execution_result()`方法，处理交易结果
- [ ] 实现成交信息记录（价格、数量、手续费）
- [ ] 实现持仓状态更新
- [ ] 实现账户净值更新
- [ ] 实现滑点过大检测（>0.5%告警）
- [ ] 编写结果处理单元测试`tests/unit/test_result_handler.py`
- **涉及文件**: `src/execution/result_handler.py`, `tests/unit/test_result_handler.py`
- **验收标准**: 交易结果正确处理并记录
- **预估工时**: 1.5小时
- **依赖关系**: 10.1, 3.4, 3.5

---

## 11. 风险控制模块开发

### 11.1 硬止损执行器
- [ ] 创建硬止损模块`src/risk/stop_loss_executor.py`
- [ ] 实现`StopLossExecutor`类
- [ ] 实现`check_stop_loss()`方法，检查止损触发
- [ ] 实现`execute_stop_loss()`方法，执行止损平仓
- [ ] 实现止损价格更新逻辑（每4小时更新，只升不降）
- [ ] 编写硬止损单元测试`tests/unit/test_stop_loss_executor.py`
- **涉及文件**: `src/risk/stop_loss_executor.py`, `tests/unit/test_stop_loss_executor.py`
- **验收标准**: 硬止损正确触发和执行
- **预估工时**: 1.5小时
- **依赖关系**: 10.1, 3.4

### 11.2 闪崩保护器
- [ ] 创建闪崩保护模块`src/risk/flash_crash_protector.py`
- [ ] 实现`FlashCrashProtector`类
- [ ] 实现`monitor_flash_crash()`方法，监控闪崩
- [ ] 闪崩条件：15分钟内下跌≥5%
- [ ] 实现`execute_flash_crash_protection()`方法，紧急平仓
- [ ] 编写闪崩保护单元测试`tests/unit/test_flash_crash_protector.py`
- **涉及文件**: `src/risk/flash_crash_protector.py`, `tests/unit/test_flash_crash_protector.py`
- **验收标准**: 闪崩正确检测并触发保护
- **预估工时**: 1.5小时
- **依赖关系**: 4.1, 10.1

### 11.3 熔断管理器
- [ ] 创建熔断管理模块`src/risk/circuit_breaker.py`
- [ ] 实现`CircuitBreaker`类
- [ ] 实现`check_drawdown()`方法，检查全局回撤
- [ ] 全局回撤熔断：回撤≥20%清仓并暂停30天
- [ ] 实现黑天鹅熔断逻辑：5分钟跌幅≥3%平仓50%，24小时跌幅≥15%清仓并暂停7天
- [ ] 实现异常波动熔断：波动>10%且浮亏>8%强制平仓
- [ ] 实现熔断状态管理（暂停/恢复）
- [ ] 实现熔断30天后自动恢复
- [ ] 编写熔断管理单元测试`tests/unit/test_circuit_breaker.py`
- **涉及文件**: `src/risk/circuit_breaker.py`, `tests/unit/test_circuit_breaker.py`
- **验收标准**: 熔断条件正确检测，熔断状态正确管理
- **预估工时**: 2.5小时
- **依赖关系**: 3.5, 10.1

### 11.4 风险控制协调器
- [ ] 创建风控协调模块`src/risk/risk_controller.py`
- [ ] 实现`RiskController`类，协调所有风控子模块
- [ ] 实现`run_risk_check()`方法，执行完整风控检查
- [ ] 实现风控优先级：风控指令优先于信号指令（一票否决权）
- [ ] 实现风控告警通知
- [ ] 编写风控协调单元测试`tests/unit/test_risk_controller.py`
- **涉及文件**: `src/risk/risk_controller.py`, `tests/unit/test_risk_controller.py`
- **验收标准**: 风控流程正确执行，优先级正确
- **预估工时**: 2小时
- **依赖关系**: 11.1, 11.2, 11.3

---

## 12. 监控告警模块开发

### 12.1 交易事件通知器
- [ ] 创建交易通知模块`src/monitor/trade_notifier.py`
- [ ] 实现`TradeNotifier`类
- [ ] 实现`notify_trade()`方法，发送交易通知到Telegram
- [ ] 通知内容：交易类型、价格、数量、持仓变化、盈亏情况
- [ ] 实现敏感数据过滤（不包含余额、持仓大小）
- [ ] 编写交易通知单元测试`tests/unit/test_trade_notifier.py`
- **涉及文件**: `src/monitor/trade_notifier.py`, `tests/unit/test_trade_notifier.py`
- **验收标准**: 交易通知正确发送，敏感数据已过滤
- **预估工时**: 1小时
- **依赖关系**: 4.5

### 12.2 告警管理器
- [ ] 创建告警管理模块`src/monitor/alert_manager.py`
- [ ] 实现`AlertManager`类
- [ ] 实现`send_data_alert()`方法，发送数据异常告警
- [ ] 实现`send_risk_alert()`方法，发送风控告警
- [ ] 实现`send_equity_alert()`方法，发送净值回撤告警（单日回撤>5%）
- [ ] 实现告警频率控制（同类告警每5分钟一次）
- [ ] 编写告警管理单元测试`tests/unit/test_alert_manager.py`
- **涉及文件**: `src/monitor/alert_manager.py`, `tests/unit/test_alert_manager.py`
- **验收标准**: 告警正确发送，频率控制正确
- **预估工时**: 1.5小时
- **依赖关系**: 4.5

### 12.3 监控数据输出器
- [ ] 创建监控输出模块`src/monitor/metrics_exporter.py`
- [ ] 实现`MetricsExporter`类
- [ ] 实现`export_metrics()`方法，输出监控数据
- [ ] 监控数据：持仓状态、净值曲线、信号记录、风控指标
- [ ] 实现每日状态报告生成
- [ ] 实现监控数据写入本地文件（支持Grafana读取）
- [ ] 编写监控输出单元测试`tests/unit/test_metrics_exporter.py`
- **涉及文件**: `src/monitor/metrics_exporter.py`, `tests/unit/test_metrics_exporter.py`
- **验收标准**: 监控数据正确输出
- **预估工时**: 1.5小时
- **依赖关系**: 3.4, 3.5

---

## 13. 回测系统开发

### 13.1 历史数据加载器
- [ ] 创建回测数据模块`src/backtest/data_loader.py`
- [ ] 实现`BacktestDataLoader`类
- [ ] 实现`load_historical_data()`方法，加载2019至今历史数据
- [ ] 实现训练期和测试期划分（2022-01-01为界）
- [ ] 实现数据缺失处理（使用前一日填充）
- [ ] 编写数据加载单元测试`tests/unit/test_backtest_data_loader.py`
- **涉及文件**: `src/backtest/data_loader.py`, `tests/unit/test_backtest_data_loader.py`
- **验收标准**: 历史数据正确加载和划分
- **预估工时**: 1.5小时
- **依赖关系**: 3.2, 3.3

### 13.2 回测模拟器
- [ ] 创建回测模拟模块`src/backtest/backtest_engine.py`
- [ ] 实现`BacktestEngine`类
- [ ] 实现`run_backtest()`方法，执行回测
- [ ] 实现现实摩擦模拟：手续费0.1%、滑点0.1%、资金费率成本
- [ ] 实现链上数据延迟模拟（shift(2)）
- [ ] 实现模拟账户管理
- [ ] 编写回测引擎单元测试`tests/unit/test_backtest_engine.py`
- **涉及文件**: `src/backtest/backtest_engine.py`, `tests/unit/test_backtest_engine.py`
- **验收标准**: 回测正确执行，摩擦成本正确扣除
- **预估工时**: 3小时
- **依赖关系**: 13.1, 8.1, 9.3

### 13.3 回测评估指标计算器
- [ ] 创建回测评估模块`src/backtest/metrics_calculator.py`
- [ ] 实现`MetricsCalculator`类
- [ ] 实现`calculate_returns()`方法，计算年化收益率
- [ ] 实现`calculate_sharpe_ratio()`方法，计算夏普比率
- [ ] 实现`calculate_max_drawdown()`方法，计算最大回撤
- [ ] 实现`calculate_calmar_ratio()`方法，计算卡尔玛比率
- [ ] 实现`calculate_trade_stats()`方法，计算胜率、盈亏比
- [ ] 实现`calculate_excess_return()`方法，计算超额收益
- [ ] 实现回测通过标准判断（年化收益≥BTC现货90%且最大回撤≤25%）
- [ ] 编写指标计算单元测试`tests/unit/test_metrics_calculator.py`
- **涉及文件**: `src/backtest/metrics_calculator.py`, `tests/unit/test_metrics_calculator.py`
- **验收标准**: 所有评估指标计算正确
- **预估工时**: 2小时
- **依赖关系**: 13.2

### 13.4 回测报告生成器
- [ ] 创建回测报告模块`src/backtest/report_generator.py`
- [ ] 实现`ReportGenerator`类
- [ ] 实现`generate_report()`方法，生成回测报告
- [ ] 报告内容：收益曲线、风险指标、交易统计、通过标准判断
- [ ] 实现报告导出为HTML或PDF
- [ ] 编写报告生成单元测试`tests/unit/test_report_generator.py`
- **涉及文件**: `src/backtest/report_generator.py`, `tests/unit/test_report_generator.py`
- **验收标准**: 回测报告正确生成
- **预估工时**: 1.5小时
- **依赖关系**: 13.3

---

## 14. 定时调度模块开发

### 14.1 定时任务调度器
- [ ] 创建调度模块`src/scheduler/task_scheduler.py`
- [ ] 实现`TaskScheduler`类
- [ ] 实现每日数据采集任务：UTC 00:05
- [ ] 实现每日信号计算和交易执行任务：UTC 00:10
- [ ] 实现风控检查任务：每4小时
- [ ] 实现闪崩监控任务：每15分钟
- [ ] 实现止损价格更新任务：每4小时
- [ ] 实现错过执行处理（coalesce）
- [ ] 实现任务持久化
- [ ] 编写调度器单元测试`tests/unit/test_task_scheduler.py`
- **涉及文件**: `src/scheduler/task_scheduler.py`, `tests/unit/test_task_scheduler.py`
- **技术要点**: APScheduler, CronTrigger
- **验收标准**: 所有定时任务正确调度执行
- **预估工时**: 2小时
- **依赖关系**: 5.6, 9.3, 11.4

---

## 15. 主程序入口

### 15.1 主程序入口
- [ ] 创建主程序`main.py`
- [ ] 实现系统初始化流程（配置加载、数据库初始化、日志初始化）
- [ ] 实现API权限验证
- [ ] 实现调度器启动
- [ ] 实现优雅退出处理（保存状态、关闭连接）
- [ ] 实现健康检查接口
- [ ] 编写主程序集成测试`tests/integration/test_main.py`
- **涉及文件**: `main.py`, `tests/integration/test_main.py`
- **验收标准**: 系统正确启动和运行，优雅退出正常
- **预估工时**: 2小时
- **依赖关系**: 14.1

---

## 16. 单元测试补充

### 16.1 测试数据生成器
- [ ] 创建测试数据生成器`tests/fixtures/data_generator.py`
- [ ] 实现模拟行情数据生成
- [ ] 实现模拟链上数据生成
- [ ] 实现模拟交易信号生成
- [ ] 实现模拟持仓数据生成
- **涉及文件**: `tests/fixtures/data_generator.py`
- **验收标准**: 测试数据生成正确
- **预估工时**: 1小时
- **依赖关系**: 2.2

### 16.2 Mock对象工厂
- [ ] 创建Mock工厂`tests/fixtures/mock_factory.py`
- [ ] 实现OKX API Mock对象
- [ ] 实现Glassnode API Mock对象
- [ ] 实现Telegram API Mock对象
- [ ] 实现数据库Mock对象
- **涉及文件**: `tests/fixtures/mock_factory.py`
- **技术要点**: unittest.mock, pytest fixtures
- **验收标准**: Mock对象正确模拟外部依赖
- **预估工时**: 1.5小时
- **依赖关系**: 16.1

---

## 17. 集成测试开发

### 17.1 数据采集集成测试
- [ ] 创建数据采集集成测试`tests/integration/test_data_collection_flow.py`
- [ ] 测试完整数据采集流程（OKX、链上、稳定币、情绪指数）
- [ ] 测试数据完整性校验
- [ ] 测试异常数据处理
- [ ] 测试数据持久化
- **涉及文件**: `tests/integration/test_data_collection_flow.py`
- **验收标准**: 数据采集流程正确执行
- **预估工时**: 2小时
- **依赖关系**: 5.6, 16.2

### 17.2 信号计算集成测试
- [ ] 创建信号计算集成测试`tests/integration/test_signal_calculation_flow.py`
- [ ] 测试完整信号计算流程（指标计算→体制识别→信号生成）
- [ ] 测试开仓信号生成
- [ ] 测试平仓信号生成
- [ ] 测试止损信号生成
- **涉及文件**: `tests/integration/test_signal_calculation_flow.py`
- **验收标准**: 信号计算流程正确执行
- **预估工时**: 2小时
- **依赖关系**: 8.1, 16.2

### 17.3 交易执行集成测试
- [ ] 创建交易执行集成测试`tests/integration/test_trading_flow.py`
- [ ] 测试完整交易执行流程（信号→决策→执行→记录）
- [ ] 测试开仓流程
- [ ] 测试平仓流程
- [ ] 测试订单状态轮询
- [ ] 测试异常处理
- **涉及文件**: `tests/integration/test_trading_flow.py`
- **验收标准**: 交易执行流程正确执行
- **预估工时**: 2.5小时
- **依赖关系**: 10.1, 16.2

### 17.4 风险控制集成测试
- [ ] 创建风控集成测试`tests/integration/test_risk_control_flow.py`
- [ ] 测试完整风控流程
- [ ] 测试硬止损触发和执行
- [ ] 测试闪崩保护
- [ ] 测试熔断机制
- [ ] 测试风控优先级
- **涉及文件**: `tests/integration/test_risk_control_flow.py`
- **验收标准**: 风控流程正确执行
- **预估工时**: 2小时
- **依赖关系**: 11.4, 16.2

### 17.5 回测系统集成测试
- [ ] 创建回测集成测试`tests/integration/test_backtest_flow.py`
- [ ] 测试完整回测流程
- [ ] 测试回测评估指标计算
- [ ] 测试回测报告生成
- [ ] 测试回测通过标准判断
- **涉及文件**: `tests/integration/test_backtest_flow.py`
- **验收标准**: 回测流程正确执行
- **预估工时**: 2小时
- **依赖关系**: 13.4, 16.2

---

## 18. 部署配置开发

### 18.1 Docker配置
- [ ] 创建Dockerfile
- [ ] 配置Python 3.10基础镜像
- [ ] 安装系统依赖（gcc等）
- [ ] 安装Python依赖
- [ ] 创建数据目录和日志目录
- [ ] 配置环境变量
- [ ] 配置健康检查
- [ ] 配置启动命令
- **涉及文件**: `Dockerfile`
- **技术要点**: Docker多阶段构建，健康检查
- **验收标准**: Docker镜像正确构建和运行
- **预估工时**: 1.5小时
- **依赖关系**: 15.1

### 18.2 Docker Compose配置
- [ ] 创建docker-compose.yml
- [ ] 配置服务定义
- [ ] 配置环境变量注入
- [ ] 配置数据卷挂载（数据、日志、配置）
- [ ] 配置日志驱动和轮转
- [ ] 配置重启策略
- **涉及文件**: `docker-compose.yml`
- **验收标准**: Docker Compose正确编排服务
- **预估工时**: 1小时
- **依赖关系**: 18.1

### 18.3 部署脚本
- [ ] 创建部署脚本`scripts/deploy.sh`
- [ ] 实现环境检查（Docker、Docker Compose）
- [ ] 实现配置文件检查
- [ ] 实现数据库初始化
- [ ] 实现服务启动
- [ ] 实现服务停止
- [ ] 实现服务重启
- [ ] 实现日志查看
- **涉及文件**: `scripts/deploy.sh`
- **验收标准**: 部署脚本正确执行
- **预估工时**: 1.5小时
- **依赖关系**: 18.2

### 18.4 运维脚本
- [ ] 创建数据库备份脚本`scripts/backup_db.py`
- [ ] 创建日志清理脚本`scripts/clean_logs.py`
- [ ] 创建配置更新脚本`scripts/update_config.py`
- [ ] 创建健康检查脚本`scripts/health_check.py`
- [ ] 创建手动平仓脚本`scripts/manual_close.py`（紧急情况使用）
- **涉及文件**: `scripts/backup_db.py`, `scripts/clean_logs.py`, `scripts/update_config.py`, `scripts/health_check.py`, `scripts/manual_close.py`
- **验收标准**: 运维脚本正确执行
- **预估工时**: 2小时
- **依赖关系**: 18.3

---

## 19. 文档完善

### 19.1 API文档
- [ ] 创建API文档`docs/api.md`
- [ ] 文档化所有内部模块接口
- [ ] 文档化外部API调用方式
- [ ] 文档化数据模型定义
- **涉及文件**: `docs/api.md`
- **验收标准**: API文档完整清晰
- **预估工时**: 2小时
- **依赖关系**: 15.1

### 19.2 运维文档
- [ ] 创建运维文档`docs/operations.md`
- [ ] 文档化部署流程
- [ ] 文档化配置说明
- [ ] 文档化监控指标
- [ ] 文档化常见问题处理
- [ ] 文档化告警处理流程
- **涉及文件**: `docs/operations.md`
- **验收标准**: 运维文档完整清晰
- **预估工时**: 2小时
- **依赖关系**: 18.4

### 19.3 回测使用文档
- [ ] 创建回测文档`docs/backtest.md`
- [ ] 文档化回测执行方式
- [ ] 文档化回测参数配置
- [ ] 文档化回测报告解读
- [ ] 文档化策略参数调优建议
- **涉及文件**: `docs/backtest.md`
- **验收标准**: 回测文档完整清晰
- **预估工时**: 1.5小时
- **依赖关系**: 13.4

---

## 20. 最终验收测试

### 20.1 端到端测试
- [ ] 创建端到端测试`tests/e2e/test_e2e.py`
- [ ] 测试完整系统运行流程
- [ ] 测试数据采集→信号计算→交易执行→风控→监控完整链路
- [ ] 测试定时任务调度
- [ ] 测试异常处理和告警
- **涉及文件**: `tests/e2e/test_e2e.py`
- **验收标准**: 系统端到端运行正确
- **预估工时**: 3小时
- **依赖关系**: 17.5

### 20.2 性能测试
- [ ] 创建性能测试`tests/performance/test_performance.py`
- [ ] 测试数据采集性能（5分钟内完成）
- [ ] 测试信号计算性能（30秒内完成）
- [ ] 测试订单执行性能（10秒内完成）
- [ ] 测试内存占用（≤2GB）
- [ ] 测试CPU使用率（≤50%）
- **涉及文件**: `tests/performance/test_performance.py`
- **验收标准**: 所有性能指标达标
- **预估工时**: 2小时
- **依赖关系**: 20.1

### 20.3 安全测试
- [ ] 创建安全测试`tests/security/test_security.py`
- [ ] 测试API密钥脱敏
- [ ] 测试敏感数据过滤
- [ ] 测试权限控制
- [ ] 测试审计日志记录
- **涉及文件**: `tests/security/test_security.py`
- **验收标准**: 所有安全要求达标
- **预估工时**: 1.5小时
- **依赖关系**: 20.1

---

## 任务统计汇总

**总任务数**: 128个任务  
**预估总工时**: 约111小时（约14个工作日）

**任务分组统计**:
- 项目基础设施搭建: 6个任务, 7.5小时
- 数据模型层开发: 2个任务, 2.5小时
- 数据仓库层开发: 5个任务, 7小时
- 外部API接口封装层: 5个任务, 8.5小时
- 数据采集模块开发: 6个任务, 8小时
- 指标计算模块开发: 2个任务, 3.5小时
- 体制识别模块开发: 1个任务, 1.5小时
- 信号生成模块开发: 1个任务, 2.5小时
- 策略决策引擎开发: 3个任务, 5小时
- 执行网关模块开发: 2个任务, 4.5小时
- 风险控制模块开发: 4个任务, 7.5小时
- 监控告警模块开发: 3个任务, 4小时
- 回测系统开发: 4个任务, 8小时
- 定时调度模块开发: 1个任务, 2小时
- 主程序入口: 1个任务, 2小时
- 单元测试补充: 2个任务, 2.5小时
- 集成测试开发: 5个任务, 10.5小时
- 部署配置开发: 4个任务, 6小时
- 文档完善: 3个任务, 5.5小时
- 最终验收测试: 3个任务, 6.5小时

**关键路径**:
1. 基础设施 → 数据模型 → 数据仓库 → API接口 → 数据采集 → 指标计算 → 体制识别 → 信号生成 → 策略引擎 → 执行网关 → 风控 → 调度器 → 主程序 → 集成测试 → 部署

**优先级排序**:
- P0（必须）: 1-15章节（核心功能）
- P1（重要）: 16-17章节（测试）
- P2（必要）: 18章节（部署）
- P3（建议）: 19-20章节（文档和验收）

---

**文档结束**
