# AOSFT-MVP — 链上与体制感知的BTC趋势跟踪系统

**版本**: v1.0  
**核心理念**: 用5%的复杂度换取80%可把握的趋势收益  
**交易所**: OKX  

---

## 📋 项目简介

### 项目目标

构建一个生产可用的、低维护成本的自动化量化交易系统,仅交易BTC/USDT现货或1x永续合约。系统通过识别市场体制(高波动上涨/下跌、低波动震荡),结合关键链上资金信号,在上升趋势启动时入场、趋势结束时离场,在震荡和下跌环境中保持空仓或轻仓,实现稳定的超额收益。

### 预期表现

- **牛市表现**: 捕获约80%-110%的BTC涨幅
- **熊市表现**: 通过空仓/轻仓规避主跌浪,最大回撤控制在25%以内
- **震荡期表现**: 年化胜率45%-55%,盈亏比>2.0
- **长期目标**: 跑赢BTC现货持有收益20%以上(超额阿尔法)

### 核心原则

1. **极简数据**: 仅使用免费、易获取的日线价格数据、两个链上核心指标、一个情绪指数
2. **逻辑透明**: 全部规则可溯源,无黑箱,每个决策都有明确的技术或链上依据
3. **安全第一**: 牺牲部分利润以换取低回撤和高存活率,注重极端行情下的本金保护
4. **可演进**: 架构上预留扩展点,未来可逐步加入微观结构、情绪分析等模块

---

## 🏗️ 系统架构

### 五层架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    定时调度层(Scheduler)                  │
│              Cron定时任务触发、任务编排                      │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                  数据采集层(Data Collector)               │
│      OKX行情、链上数据、稳定币数据、情绪指数采集            │
│      数据时间戳管理、数据质量评分                          │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                    风控前置拦截层(Risk Interceptor)        │
│     熔断状态检查、数据新鲜度检查、市场异常检查              │
│              一票否决权、信号拦截                          │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                  策略计算层(Strategy Engine)             │
│      指标计算、体制定义、信号生成、仓位决策                 │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                    执行层(Execution)                      │
│    订单状态机、挂单超时管理、订单异常恢复                    │
│          OKX执行网关、结果确认                             │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                    风控层(Risk Control)                   │
│      硬止损、分级熔断恢复、闪崩保护、监控告警               │
└─────────────────────────────────────────────────────────┘
```

### 核心模块列表

| 模块 | 职责 | 关键特性 |
|------|------|----------|
| **数据采集模块** | 多源数据采集、存储和管理 | 数据时间戳管理、数据质量评分 |
| **风控前置拦截模块** | 信号拦截和风控检查 | 一票否决权、熔断状态检查 |
| **指标计算模块** | 技术指标和衍生指标计算 | MA、ATR、净流入趋势计算 |
| **体制识别模块** | 市场体制判定 | 三种体制识别(BULL/BEAR/LOW_VOLATILE) |
| **信号生成模块** | 交易信号生成 | 开仓/平仓/止损信号 |
| **策略决策引擎** | 仓位管理和决策逻辑 | 频率控制、合约模式处理 |
| **风险控制模块** | 风控措施执行 | 分级熔断恢复、硬止损 |
| **执行网关** | 订单执行和管理 | 订单状态机、异常恢复 |
| **监控告警模块** | 监控和通知 | 完整监控指标体系 |
| **回测系统** | 策略验证 | 极端行情回测、参数敏感性分析 |

---

## ✨ 主要特性

### 1. 风控前置拦截机制

- **一票否决权**: 风控模块独立于策略引擎,在信号传递前进行拦截检查
- **多层检查**: 熔断状态检查、数据新鲜度检查、市场异常波动检查
- **否决记录**: 完整记录拦截原因,供审计和监控使用

### 2. 数据时间戳管理和质量评分

- **采集时间标记**: 为每个数据点标记实际采集时间和数据日期
- **新鲜度计算**: 实时计算数据延迟天数,监控数据时效性
- **质量评分**: 根据延迟自动评分(≤1天:1.0, 2天:0.8, ≥3天:0.5)
- **过期数据处理**: 延迟≥3天的数据降权使用并告警

### 3. 订单状态机和异常恢复

- **完整状态机**: PENDING → PARTIAL_FILLED → FILLED/REJECTED/CANCELLED
- **挂单超时管理**: 限价单5分钟未成交自动撤单改市价,30分钟强制撤单
- **异常恢复策略**: 部分成交超时、挂单无响应、订单拒绝等多种恢复机制
- **状态同步**: 主动查询交易所并同步订单状态

### 4. 分级熔断恢复机制

- **触发条件**: 账户回撤≥20%触发全局熔断
- **分级恢复**: 熔断后第10天恢复50%仓位,第20天恢复100%仓位
- **持续观测**: 熔断期间继续数据采集,保持系统观测状态
- **人工干预**: 支持管理员确认后提前解除熔断

### 5. 完整监控指标体系

- **数据新鲜度监控**: 实时监控各数据源最后更新时间
- **策略性能监控**: 信号胜率、盈亏比、连续亏损次数统计
- **风控触发统计**: 各类熔断累计触发次数和原因
- **API调用统计**: API调用成功率和延迟分布(P50/P95/P99)

### 6. 加强的测试策略

- **极端行情回测**: 专门测试黑天鹅场景表现(如2020年3月12日暴跌)
- **参数敏感性分析**: 对关键参数进行±20%变动测试
- **并发压力测试**: 验证定时任务并发处理能力
- **模拟盘验证**: OKX Testnet环境连续运行30天验证

---

## 🛠️ 技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **编程语言** | Python | 3.10+ | 核心开发语言 |
| **交易所接口** | CCXT | v4.0+ | OKX API统一封装 |
| **数据处理** | Pandas | v2.0+ | 时间序列数据处理 |
| **数值计算** | NumPy | v1.24+ | 高性能数组运算 |
| **定时任务** | APScheduler | v3.10+ | Cron定时调度 |
| **数据库** | SQLite | 3 | 轻量级数据存储 |
| **通知推送** | python-telegram-bot | v20+ | Telegram通知 |
| **HTTP请求** | Requests | v2.31+ | API调用 |
| **容器化** | Docker | - | 环境封装部署 |

### 可选依赖

- **TA-Lib**: 技术指标库(加速计算)
- **Plotly/Dash**: 可视化监控面板
- **Grafana + InfluxDB**: 生产级监控方案

---

## 📁 项目结构

```
aosft_mvp/
├── src/                      # 源代码
│   ├── collectors/           # 数据采集模块
│   │   ├── okx_collector.py       # OKX行情采集器
│   │   ├── onchain_collector.py   # 链上数据采集器
│   │   ├── stablecoin_collector.py # 稳定币数据采集器
│   │   └── sentiment_collector.py # 情绪指数采集器
│   ├── indicators/           # 指标计算模块
│   │   ├── ma.py                  # 移动平均线计算
│   │   ├── atr.py                 # ATR计算
│   │   └── trend.py               # 趋势指标计算
│   ├── regime/               # 体制识别模块
│   │   ├── detector.py            # 体制定义器
│   │   └── classifier.py          # 体制分类器
│   ├── signals/              # 信号生成模块
│   │   ├── open_signal.py         # 开仓信号生成器
│   │   ├── close_signal.py        # 平仓信号生成器
│   │   └── stop_signal.py         # 止损信号生成器
│   ├── strategy/             # 策略决策模块
│   │   ├── engine.py              # 策略引擎
│   │   ├── position.py            # 仓位管理器
│   │   └── frequency.py           # 频率控制器
│   ├── execution/            # 交易执行模块
│   │   ├── gateway.py             # OKX执行网关
│   │   ├── order_state_machine.py # 订单状态机
│   │   ├── timeout_manager.py     # 挂单超时管理器
│   │   └── recovery.py            # 订单异常恢复器
│   ├── risk/                 # 风险控制模块
│   │   ├── interceptor.py         # 风控前置拦截器
│   │   ├── stop_loss.py           # 硬止损执行器
│   │   ├── circuit_breaker.py     # 熔断管理器
│   │   └── recovery_manager.py    # 分级恢复管理器
│   ├── monitor/              # 监控告警模块
│   │   ├── telegram.py            # Telegram推送器
│   │   ├── metrics.py             # 监控指标统计
│   │   └── dashboard.py           # 监控数据输出
│   ├── backtest/             # 回测系统
│   │   ├── engine.py              # 回测引擎
│   │   ├── extreme_scenarios.py   # 极端行情回测
│   │   └── sensitivity.py         # 参数敏感性分析
│   ├── scheduler/            # 定时调度模块
│   │   └── cron.py                # Cron任务管理
│   ├── models/               # 数据模型
│   │   ├── ohlcv.py               # 行情数据模型
│   │   ├── signal.py              # 信号数据模型
│   │   ├── position.py            # 持仓数据模型
│   │   └── order.py               # 订单数据模型
│   └── utils/                # 工具函数
│       ├── db.py                  # 数据库工具
│       ├── logger.py              # 日志工具
│       └── config.py              # 配置管理
├── tests/                    # 测试代码
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   └── extreme/                   # 极端场景测试
├── config/                   # 配置文件
│   ├── settings.yaml              # 系统配置
│   ├── okx.yaml                   # OKX配置
│   └── risk.yaml                  # 风控配置
├── data/                     # 数据存储
│   ├── aosft.db                   # SQLite数据库
│   └── backup/                    # 数据备份
├── logs/                     # 日志文件
│   ├── system.log                 # 系统日志
│   ├── trade.log                  # 交易日志
│   └── risk.log                   # 风控日志
├── scripts/                  # 脚本工具
│   ├── init_db.py                 # 数据库初始化
│   ├── backfill_data.py           # 历史数据回填
│   └── check_status.py            # 状态检查工具
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖清单
├── Dockerfile                # Docker镜像定义
├── docker-compose.yml        # Docker编排文件
└── README.MD                 # 项目说明文档
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Docker (可选,推荐使用)
- SQLite 3
- Git 2.0+

### Git仓库初始化

```bash
# 克隆项目仓库
git clone https://github.com/your-org/aosft-mvp.git
cd aosft-mvp

# 配置Git用户信息(如尚未配置)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 查看当前分支
git branch
```

### Git版本管理规范

#### 分支管理策略

本项目采用Git Flow工作流:

- **master/main**: 生产分支,仅存放稳定发布版本
- **develop**: 开发分支,日常开发集成
- **feature/***: 功能分支,开发新功能
- **hotfix/***: 紧急修复分支,修复生产问题
- **release/***: 发布分支,版本发布准备

#### 分支命名规范

```
feature/功能描述    # 例如: feature/add-backtest-module
hotfix/问题描述     # 例如: hotfix/fix-order-timeout
release/版本号      # 例如: release/v1.1
```

#### 提交代码流程

```bash
# 1. 从develop分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature

# 2. 开发完成后提交代码
git add .
git commit -m "feat: 添加回测模块核心功能"

# 3. 推送到远程仓库
git push origin feature/your-feature

# 4. 创建Pull Request(PR)
# 在GitHub/GitLab上创建PR,目标分支为develop

# 5. 代码审查通过后合并
# 由项目维护者审查并合并PR
```

#### 提交信息规范

遵循Conventional Commits规范:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型(type)**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整(不影响功能)
- `refactor`: 重构代码
- `test`: 添加测试
- `chore`: 构建或辅助工具变动
- `perf`: 性能优化

**示例**:

```bash
# 新功能
git commit -m "feat(strategy): 添加仓位管理模块"

# 修复bug
git commit -m "fix(execution): 修复订单超时处理逻辑"

# 文档更新
git commit -m "docs(readme): 补充Git版本管理说明"

# 重构代码
git commit -m "refactor(risk): 优化熔断管理器实现"

# 多行提交信息
git commit -m "feat(backtest): 实现参数敏感性分析" -m "- 支持单参数变动分析" -m "- 支持多参数组合分析" -m "Closes #123"
```

### 安装步骤

#### 方式一: 直接安装

```bash
# 1. 克隆项目
git clone https://github.com/your-org/aosft-mvp.git
cd aosft-mvp

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python scripts/init_db.py

# 5. 配置环境变量
cp config/settings.yaml.example config/settings.yaml
# 编辑settings.yaml填入API密钥等配置
```

#### 方式二: Docker部署(推荐)

```bash
# 1. 克隆项目
git clone <repository-url>
cd aosft_mvp

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件填入API密钥

# 3. 构建并启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 配置说明

#### 必需配置项

在`config/settings.yaml`中配置以下关键参数:

```yaml
# OKX交易所配置
okx:
  api_key: "your-api-key"
  secret: "your-secret-key"
  password: "your-api-password"
  account_type: "spot"  # "spot"或"swap"

# 链上数据配置
glassnode:
  api_key: "your-glassnode-key"

# Telegram通知配置
telegram:
  bot_token: "your-bot-token"
  chat_id: "your-chat-id"

# 策略参数
strategy:
  ma_period: 20              # 趋势均线周期
  atr_period: 14             # ATR计算周期
  position_ratio: 0.5        # 仓位占比(50%)
  max_drawdown: 0.20         # 最大回撤熔断阈值

# 风控参数
risk:
  stop_loss_atr_multiplier: 2.0   # 止损ATR倍数
  circuit_breaker_days: 30        # 熔断暂停天数
  recovery_stage1_days: 10        # 分级恢复第一阶段
  recovery_stage2_days: 20        # 分级恢复第二阶段
```

### 运行方式

#### 开发环境运行

```bash
# 运行主程序
python main.py

# 运行回测
python scripts/backfill_data.py --start 2019-01-01 --end 2024-01-01

# 检查系统状态
python scripts/check_status.py
```

#### 生产环境运行(Docker)

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看实时日志
docker-compose logs -f aosft-mvp
```

---

## 📚 文档链接

| 文档 | 路径 | 说明 |
|------|------|------|
| **需求规格说明书** | [.codeartsdoer/specs/aosft-mvp/spec.md](.codeartsdoer/specs/aosft-mvp/spec.md) | 详细的需求定义和业务规则 |
| **技术架构设计** | [.codeartsdoer/specs/aosft-mvp/design.md](.codeartsdoer/specs/aosft-mvp/design.md) | 完整的技术实现方案 |
| **编码任务规划** | [.codeartsdoer/specs/aosft-mvp/tasks.md](.codeartsdoer/specs/aosft-mvp/tasks.md) | 开发任务分解和进度规划 |

---

## ⚠️ 风险提示

### 核心风险说明

**本系统基于历史规律和逻辑推理构建,不保证未来盈利。**

### 主要脆弱性

1. **黑天鹅事件风险**
   - 可能出现远超2×ATR的跳空缺口,导致止损滑点巨大
   - 极端市场情况下流动性枯竭,无法及时平仓

2. **链上信号失效风险**
   - 当BTC定价权转移至传统金融工具(如ETF)时,交易所链上数据可能失去预测能力
   - 链上数据来源单一,API故障可能导致信号延迟

3. **长期震荡市风险**
   - 可能产生持续6-12个月的小额亏损
   - 考验执行纪律和资金管理能力

4. **技术故障风险**
   - 脚本错误、API限制、服务器宕机等可能导致无法平仓
   - 网络延迟可能导致订单执行价格偏离预期

### 投资者提示

- **仅使用可承受全部损失的资金参与**
- **充分理解系统策略逻辑和风险承受能力**
- **定期检查系统运行状态和交易记录**
- **极端市场环境下考虑人工干预**

---

## 📊 系统监控

### 每日必查清单

- [ ] 前一交易日信号是否正确执行
- [ ] 数据是否全部拉取成功
- [ ] 当前持仓、止损价、浮盈浮亏
- [ ] 风控指标: 回撤是否接近15%预警线
- [ ] 数据新鲜度: 是否有数据源延迟

### 自动化告警

系统通过Telegram Bot自动推送以下告警:

- 开仓/平仓事件即时通知
- 数据采集失败告警
- 净值单日回撤超5%告警
- 极端行情熔断触发告警
- 订单异常处理通知

---

## 🔄 系统维护

### 定期Review

- **每两周**: 人工复盘所有交易,检查是否有规则外操作
- **每季度**: 重新评估参数(ATR倍数、均线周期等),微调不超过20%
- **每月**: 数据完整性核对,检查累积误差

### 日志管理

- 日志自动轮转,保留最近90天
- 交易日志、系统日志、风控日志分离存储
- 异常情况自动升级告警

---

## 📝 版本历史

### v1.0 (2026-05-18)

**重大更新**:

- ✅ 交易所从Binance迁移至OKX
- ✅ 新增风控前置拦截层,实现一票否决权
- ✅ 实现数据时间戳管理和质量评分机制
- ✅ 实现完整订单状态机和异常恢复机制
- ✅ 实现分级熔断恢复机制(10天50%,20天100%)
- ✅ 实现完整监控指标体系
- ✅ 加强测试策略(极端行情、参数敏感性、并发压力测试)

**技术改进**:

- 架构优化为六层设计(增加风控前置拦截层)
- 完善数据模型和数据库设计
- 增强Docker部署支持
- 完善配置管理和参数化

---

## 📧 联系方式

如有问题或建议,请通过以下方式联系:

- **项目Issues**: 提交GitHub Issue
- **Telegram群组**: [待补充]

---

**免责声明**: 本系统仅供学习和研究使用,不构成任何投资建议。使用本系统进行实盘交易的一切后果由使用者自行承担。
