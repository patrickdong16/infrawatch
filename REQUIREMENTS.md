# InfraWatch 需求规格说明书

> **版本**: v1.0  
> **日期**: 2026-01-29  
> **状态**: 初始版本  
> **关联文档**: [PRD](./docs/AI_Infra_Monitor_PRD.md) | [TDD](./docs/AI_Infra_Monitor_TDD.md) | [监测体系](./docs/AI_基建可持续拐点监测体系_v2.1.md)

---

## 一、产品定位

**AI Infrastructure Sustainability Monitor (InfraWatch)** 是一个面向专业科技投资者的 **AI基建可持续性先行指标监测平台**，通过追踪价格信号、企业采用数据和财务指标，帮助用户比市场更早6-12个月识别AI产业周期的拐点。

### 核心原则

| 原则 | 执行要求 |
|------|----------|
| **只呈现事实** | 系统输出信号，判断留给用户，不做预测 |
| **一手数据优先** | 仅采集官方披露、定价页、财报原文 |
| **信号 > 噪音** | 只在显著变动时推送，避免信息过载 |
| **透明可溯源** | 每个数据点都有原始来源链接 |

---

## 二、监测体系架构

### 2.1 因果链条

```
E板块 (供应链价格: HBM/DRAM/封装)
    ↓ 6-12月传导
C板块 (算力供需: 云服务/GPU租赁价格)
    ↓
B板块 (推理现金流: 模型API价格)
    ↓
M01代理指标 (基建自养能力)
    ↓
A板块 (应用层: 企业采用信号)
    ↓
D板块 (巨头财务健康度)
```

### 2.2 指标板块详情

#### A板块：企业应用采用信号

| metric_id | 指标名称 | 定义 | 来源 | 频率 |
|-----------|----------|------|------|------|
| A1 | ServiceNow Pro Plus 渗透率 | Pro Plus SKU 占总ACV比例 | 财报 | 季度 |
| A2 | M365 Copilot 万席客户数 | 拥有 >10,000 付费坐席的客户数量 | 微软财报 | 季度 |
| A3 | Salesforce Agentforce 付费转化率 | 付费交易数 / 总交易数 | 财报 | 季度 |
| A4 | 云厂商AI贡献点数 | AI对云收入增长的贡献百分点 | 财报 | 季度 |
| A5 | 云厂商积压订单 | 长期合同总额及同比变化 | 财报 | 季度 |

#### B板块：模型API价格信号

| metric_id | 指标名称 | 监测对象 | 频率 |
|-----------|----------|----------|------|
| B1 | 旗舰模型输入价格 | GPT-4o, Claude 3.5, Gemini 1.5 Pro, DeepSeek-V3 | 周更 |
| B2 | 旗舰模型输出价格 | 同上 | 周更 |
| B3 | 经济型模型价格 | GPT-4o-mini, Claude Haiku, Gemini Flash | 周更 |
| B4 | 中国厂商锚定价 | DeepSeek, Qwen, GLM 等 | 周更 |

**派生指标**: `B_price_index`, `B_china_discount`, `B_qoq_deflation`

#### C板块：算力供需信号

| metric_id | 指标名称 | 监测对象 | 频率 |
|-----------|----------|----------|------|
| C1 | GPU裸机租赁价格 | H100/H200/B200 | 周更 |
| C2 | 托管推理服务价格 | Azure OpenAI, AWS Bedrock, Vertex AI | 周更 |
| C3 | Spot/抢占式折扣幅度 | AWS Spot, GCP Preemptible, Azure Spot | 周更 |
| C4 | 云GPU实例价格 | ND H100 v5, p5.48xlarge, a3-highgpu-8g | 月更 |

**派生指标**: `C_rental_index`, `C_spot_discount`, `C_hyperscaler_premium`

#### D板块：巨头财务健康度

| metric_id | 指标名称 | 监测对象 | 来源 | 频率 |
|-----------|----------|----------|------|------|
| D1 | 资本支出绝对值 | MSFT, AMZN, GOOGL, META | 财报 | 季度 |
| D2 | AI年化收入 (Run-Rate) | 官方披露的AI相关收入 | 财报 | 季度 |
| D3 | 云业务运营利润率 | Azure, AWS, GCP | 财报 | 季度 |
| D4 | AI对云增长贡献 | 官方披露的百分点贡献 | 财报 | 季度 |

#### E板块：供应链价格信号

| metric_id | 指标名称 | 监测对象 | 来源 | 频率 |
|-----------|----------|----------|------|------|
| E1 | HBM3e 合约价格 | SK海力士、三星、美光报价 | TrendForce | 月度 |
| E2 | 服务器DRAM价格指数 | DDR5 服务器内存现货价 | DRAMeXchange | 周度 |
| E3 | NVIDIA GPU ASP估算 | H100/H200/B200 平均售价 | 渠道调研 | 季度 |
| E4 | 台积电CoWoS产能利用率 | 先进封装产能紧张度 | 供应链调研 | 季度 |
| E5 | HBM出货量增速 | SK海力士/三星出货同比 | 财报 | 季度 |

**派生指标**: `E_hbm_premium`, `E_memory_cost_index`, `E_supply_tightness`, `E_gpu_margin_proxy`

### 2.3 M01代理指标

**公式**: `M01 = AI推理收入 / AI相关资产年化折旧`

| M01 区间 | 状态判定 |
|----------|----------|
| < 0.3 | 严重补贴期，高风险 |
| 0.3 - 0.7 | 过渡期，需观察趋势 |
| 0.7 - 1.0 | 接近自养，健康 |
| > 1.0 | 完全自养，可持续 |

---

## 三、阶段判定规则

### 3.1 四阶段模型

| 阶段 | 名称 | 触发条件 |
|------|------|----------|
| **S0** | 不可持续 | M01_high < 0.3 **且** B_qoq_deflation > 15% **且** C_spot_discount > 40% |
| **S1** | 临界过渡 | M01 在 0.3-0.7 区间 **或** A板块指标连续两季正增长 |
| **S2** | 早期自养 | M01_low > 0.7 **且** C_rental_index 环比变化 < ±5% **且** E_supply_tightness 稳定 |
| **S3** | 成熟工业化 | M01_low > 1.0 **且** B_price_index 下降 **但** D3 云利润率稳定 |

### 3.2 信号类型

| signal_type | 定义 | 触发条件示例 |
|-------------|------|-------------|
| `price_move` | 价格显著变动 | B/C板块指标环比 > 10% |
| `adoption_inflection` | 采用率拐点 | A板块指标环比加速 > 20% |
| `coverage_threshold` | 覆盖率跨越阈值 | M01 跨越 0.3/0.7/1.0 边界 |
| `supply_demand_shift` | 供需格局变化 | C_spot_discount 变化 > 10pp |
| `disclosure_change` | 披露口径变化 | 厂商停止/开始披露某指标 |
| `supply_chain_alert` | 供应链异动 | E1/E4 显著变化 |

---

## 四、功能模块规格

### 4.1 MVP阶段 (Phase 1)

| 模块 | 优先级 | 功能描述 |
|------|--------|----------|
| **P1 价格监测中心** | P0 | B+C板块价格追踪与可视化 |
| **P2 阶段仪表盘** | P0 | 当前周期阶段判定与展示 |
| **P3 信号中心** | P0 | 信号日志查看与推送管理 |

### 4.2 Phase 2

| 模块 | 优先级 | 功能描述 |
|------|--------|----------|
| **P4 财报数据管理** | P1 | A+D板块季度数据录入与展示 |
| **P5 M01覆盖率分析** | P1 | 推理覆盖率计算与趋势 |
| **P6 供应链监测中心** | P1 | E板块HBM/DRAM/GPU ASP追踪 |
| **P7 数据导出** | P2 | CSV/图表导出 |

### 4.3 Phase 3 (v1.1 新增功能)

| 模块 | 优先级 | 功能描述 | 状态 |
|------|--------|----------|------|
| **P8 厂商价格指数** | P1 | 各厂商加权平均价格对比，36.5x 差距横幅 | ✅ 已实现 |
| **P9 AI巨头财务指标** | P1 | EODHD数据源，收入/CapEx增速对比图表 | ✅ 已实现 |
| **P10 价格趋势显示** | P1 | 周环比/月环比趋势列，fallback模拟趋势 | ✅ 已实现 |

#### P8 厂商价格指数详情

- **展示位置**: 价格监测页面顶部
- **数据来源**: B板块价格数据
- **计算逻辑**: 按旗舰(1.0)、中端(0.5)、经济(0.3)加权平均
- **厂商对比**: 显示最高价厂商与最低价厂商的倍数关系
- **趋势显示**: 月环比变化

#### P9 AI巨头财务指标详情

- **展示位置**: Dashboard 三栏布局中间
- **数据来源**: EODHD API (通过 MCP)
- **监控公司**: MSFT, GOOGL, AMZN, META, NVDA, TSLA
- **核心指标**:
  - 季度收入及 QoQ 增速
  - CapEx (资本支出) 及 QoQ 增速
  - CapEx/收入比率
- **可视化**: 收入增速 vs CapEx增速双曲线图 (Recharts)

---

## 五、技术规格

### 5.1 技术栈

| 层级 | 选型 | 版本 |
|------|------|------|
| **前端** | Next.js + Tailwind + shadcn/ui | 14.x |
| **图表** | Recharts | 2.x |
| **后端** | Python FastAPI | 0.110+ |
| **ORM** | SQLAlchemy | 2.x |
| **数据库** | PostgreSQL + TimescaleDB | 16 + 2.x |
| **缓存/队列** | Redis | 7.x |
| **任务队列** | Celery | 5.x |
| **爬虫** | Playwright | 1.x |
| **部署** | Vercel (前端) + Railway (后端) | - |

### 5.2 项目结构

```
infrawatch/
├── docs/                      # 技术文档
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/           # API 路由
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # 业务逻辑
│   │   ├── repositories/     # 数据访问
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── core/             # 核心模块
│   │   └── domain/           # 领域逻辑
│   └── workers/
│       ├── tasks/            # Celery 任务
│       └── spiders/          # 爬虫模块
│           ├── sector_b/     # B板块爬虫
│           ├── sector_c/     # C板块爬虫
│           └── sector_e/     # E板块爬虫
└── frontend/                  # Next.js 前端
    ├── app/                  # App Router
    ├── components/           # React 组件
    └── lib/                  # 工具库
```

### 5.3 数据库核心表

| 表名 | 用途 |
|------|------|
| `providers` | 供应商信息 (OpenAI, Lambda等) |
| `skus` | SKU信息 (gpt-4o, h100-80gb等) |
| `price_records` | 价格时序数据 (TimescaleDB Hypertable) |
| `supply_chain_prices` | 供应链价格数据 (E板块) |
| `signal_log` | 信号日志 |
| `derived_metrics` | 派生指标快照 |
| `stage_snapshots` | 阶段判定快照 |
| `financial_records` | 财报数据 |

### 5.4 API端点规范

| 模块 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 价格 | GET | `/api/v1/prices/latest` | 获取最新价格 |
| 价格 | GET | `/api/v1/prices/history` | 获取历史价格 |
| 价格 | GET | `/api/v1/prices/indices` | 获取派生指数 |
| 价格 | GET | `/api/v1/prices/provider-indices` | **[新增]** 厂商价格指数对比 |
| 信号 | GET | `/api/v1/signals` | 获取信号列表 |
| 信号 | PATCH | `/api/v1/signals/{id}/read` | 标记已读 |
| 阶段 | GET | `/api/v1/stage/current` | 获取当前阶段 |
| 供应链 | GET | `/api/v1/supply-chain/latest` | 供应链价格 |
| 供应链 | GET | `/api/v1/supply-chain/indices` | 供应链价格指数 |
| 供应链 | GET | `/api/v1/supply-chain/config-history` | 历史价格配置 |
| 财务 | GET | `/api/v1/financials/ai-metrics` | **[新增]** AI巨头财务指标 |
| 财务 | GET | `/api/v1/financials/growth-comparison` | **[新增]** 收入/CapEx增速对比 |

---

## 六、数据采集规格

### 6.1 B板块数据源

| Provider | 采集方式 | 频率 | URL |
|----------|----------|------|-----|
| OpenAI | 爬虫 | 每日 | platform.openai.com/docs/pricing |
| Anthropic | 爬虫 | 每日 | anthropic.com/pricing |
| Google | 爬虫 | 每日 | ai.google.dev/pricing |
| DeepSeek | 爬虫 | 每日 | platform.deepseek.com |

### 6.2 C板块数据源

| Provider | 采集方式 | 频率 | URL |
|----------|----------|------|-----|
| Lambda Labs | 爬虫 | 每日 | lambdalabs.com/service/gpu-cloud |
| CoreWeave | 爬虫 | 每日 | coreweave.com/pricing |
| RunPod | API | 每日 | runpod.io/gpu-instance/pricing |
| Vast.ai | API | 每日 | vast.ai |

### 6.3 E板块数据源

| 数据源 | URL | 数据类型 | 订阅要求 |
|--------|-----|----------|----------|
| TrendForce | trendforce.com | HBM/DRAM价格 | 付费 |
| DRAMeXchange | dramexchange.com | DRAM现货价 | 付费 |
| SK海力士IR | skhynix.com/ir | HBM出货量 | 免费 |
| 台积电IR | investor.tsmc.com | 封装产能 | 免费 |

---

## 七、验收标准

### 7.1 MVP成功标准

| 指标 | 目标 |
|------|------|
| 数据覆盖 | B板块 6个厂商 + C板块 7个厂商 |
| 数据新鲜度 | B/C板块价格延迟 < 24小时 |
| 信号准确率 | 价格变动信号无遗漏 |
| 页面响应 | 核心页面3秒内加载完成 |

### 7.2 API响应格式

**成功响应**:
```json
{
  "success": true,
  "data": { ... }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": { "field": "start_date" }
  }
}
```

---

## 八、版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-01-29 | 初始版本，基于PRD/TDD整合 |
| v1.1 | 2026-01-30 | 新增 Phase 3: 厂商价格指数、EODHD财务集成、价格趋势显示 |
