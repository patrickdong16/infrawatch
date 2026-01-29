# AI 基建可持续性监测平台 - 技术设计文档 (TDD)

**项目代号**: InfraWatch  
**版本**: v1.0  
**日期**: 2026年1月  
**架构师**: Claude  
**关联文档**: PRD v1.0, 监测体系 v2.0

---

## 一、文档概述

### 1.1 目的

本文档定义 AI 基建可持续性监测平台的整体技术架构、模块设计、接口规范、数据模型和部署方案，为开发团队提供实施指南。

### 1.2 范围

- MVP阶段：价格监测（B/C板块）、阶段仪表盘、信号中心
- Phase 2：财报数据管理、M01分析、数据导出

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| B板块 | 模型API定价数据（OpenAI, Anthropic等） |
| C板块 | GPU租赁/云服务价格数据 |
| A板块 | 企业应用采用率数据 |
| D板块 | 巨头财务数据 |
| Signal | 指标异动触发的事件 |
| Spider | 针对特定数据源的爬虫模块 |

---

## 二、系统架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 客户端层                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │   Web App   │  │   Email     │  │  Webhook    │                         │
│  │  (Next.js)  │  │   Client    │  │  Consumer   │                         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                         │
└─────────┼────────────────┼────────────────┼─────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API 网关层                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ /prices  │  │ /signals │  │ /stage   │  │ /admin   │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              业务服务层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Price     │  │   Signal    │  │   Stage     │  │  Metrics    │        │
│  │   Service   │  │   Service   │  │   Service   │  │  Service    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         └────────────────┴────────────────┴────────────────┘               │
│                     Domain Models / Repositories                            │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据采集层                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Celery Workers                                  │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │   │
│  │  │ B-Sector  │  │ C-Sector  │  │  Derived  │  │   Alert   │        │   │
│  │  │ Spiders   │  │ Spiders   │  │  Metrics  │  │  Sender   │        │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Celery Beat (Scheduler)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据存储层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │ PostgreSQL  │  │   Redis     │  │    S3       │                         │
│  │ TimescaleDB │  │   Cache     │  │  Backups    │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术选型决策

| 层级 | 选型 | 版本 | 决策理由 |
|------|------|------|----------|
| **前端框架** | Next.js | 14.x | App Router、SSR/SSG支持、Vercel原生部署 |
| **UI组件** | shadcn/ui + Tailwind | - | 现代设计系统、高度可定制 |
| **图表库** | Recharts | 2.x | React原生、声明式API、轻量 |
| **后端框架** | FastAPI | 0.110+ | 异步支持、自动OpenAPI文档、类型安全 |
| **ORM** | SQLAlchemy | 2.x | 成熟稳定、支持异步 |
| **数据库** | PostgreSQL + TimescaleDB | 16 + 2.x | 时序数据优化、SQL兼容 |
| **缓存/队列** | Redis | 7.x | Celery Broker、API缓存 |
| **任务队列** | Celery | 5.x | 成熟的分布式任务框架 |
| **爬虫引擎** | Playwright | 1.x | 支持现代JS渲染页面 |

### 2.3 部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Cloudflare (CDN)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│       Vercel          │       │       Railway         │
│    (Frontend)         │       │      (Backend)        │
│  ┌─────────────────┐  │       │  ┌─────────────────┐  │
│  │   Next.js App   │  │       │  │  FastAPI x2     │  │
│  └─────────────────┘  │       │  │  Celery Worker  │  │
│                       │       │  │  Celery Beat    │  │
└───────────────────────┘       └───────────┬───────────┘
                                            │
                            ┌───────────────┴───────────────┐
                            ▼                               ▼
                ┌───────────────────────┐       ┌───────────────────────┐
                │    Railway Redis      │       │   Neon PostgreSQL     │
                └───────────────────────┘       └───────────────────────┘
```

**MVP部署成本**: ~$99/月

---

## 三、项目结构

### 3.1 后端项目结构

```
infrawatch-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理
│   │
│   ├── api/v1/                    # API 路由层
│   │   ├── router.py
│   │   ├── prices.py
│   │   ├── signals.py
│   │   ├── stage.py
│   │   └── admin.py
│   │
│   ├── schemas/                   # Pydantic 模型
│   │   ├── price.py
│   │   ├── signal.py
│   │   └── stage.py
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── price_service.py
│   │   ├── signal_service.py
│   │   └── stage_service.py
│   │
│   ├── repositories/              # 数据访问层
│   │   ├── price_repo.py
│   │   ├── signal_repo.py
│   │   └── metrics_repo.py
│   │
│   ├── models/                    # SQLAlchemy 模型
│   │   ├── price.py
│   │   ├── signal.py
│   │   └── financial.py
│   │
│   ├── core/                      # 核心模块
│   │   ├── database.py
│   │   ├── redis.py
│   │   └── exceptions.py
│   │
│   └── domain/                    # 领域逻辑
│       ├── stage_engine.py
│       ├── signal_detector.py
│       └── metrics_calculator.py
│
├── workers/                       # Celery Workers
│   ├── celery_app.py
│   ├── tasks/
│   │   ├── spider_tasks.py
│   │   ├── metrics_tasks.py
│   │   └── alert_tasks.py
│   │
│   └── spiders/                   # 爬虫模块
│       ├── base.py
│       ├── registry.py
│       ├── sector_b/              # B板块爬虫
│       │   ├── openai.py
│       │   ├── anthropic.py
│       │   └── deepseek.py
│       └── sector_c/              # C板块爬虫
│           ├── lambda_labs.py
│           └── runpod.py
│
├── migrations/                    # Alembic 迁移
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### 3.2 前端项目结构

```
infrawatch-frontend/
├── app/                           # Next.js App Router
│   ├── layout.tsx
│   ├── page.tsx                   # Dashboard
│   ├── prices/page.tsx
│   ├── signals/page.tsx
│   └── stage/page.tsx
│
├── components/
│   ├── ui/                        # shadcn/ui 组件
│   ├── charts/                    # 图表组件
│   │   ├── PriceTrendChart.tsx
│   │   ├── StageGauge.tsx
│   │   └── SparkLine.tsx
│   ├── dashboard/
│   └── layout/
│
├── lib/
│   ├── api/                       # API 客户端
│   ├── hooks/                     # 自定义 Hooks
│   └── utils/
│
├── types/
├── next.config.js
└── package.json
```

---

## 四、数据模型设计

### 4.1 ER 图

```
┌─────────────────────┐       ┌─────────────────────┐
│    price_records    │       │      providers      │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │       │ id (PK)             │
│ recorded_at         │──────>│ code                │
│ provider_id (FK)    │       │ name                │
│ sku_id (FK)         │       │ sector (B/C/E)      │
│ price_type          │       │ pricing_page_url    │
│ price               │       └─────────────────────┘
│ currency            │
│ source_url          │       ┌─────────────────────┐
└─────────────────────┘       │        skus         │
      (TimescaleDB            ├─────────────────────┤
       Hypertable)            │ id (PK)             │
                              │ provider_id (FK)    │
                              │ code                │
┌─────────────────────┐       │ name                │
│   derived_metrics   │       │ category            │
├─────────────────────┤       └─────────────────────┘
│ id (PK)             │
│ calculated_at       │       ┌─────────────────────┐
│ metric_name         │       │    signal_log       │
│ value               │       ├─────────────────────┤
│ value_low           │       │ id (PK)             │
│ value_high          │       │ triggered_at        │
│ company             │       │ signal_type         │
│ metadata (JSONB)    │       │ severity            │
└─────────────────────┘       │ description         │
                              │ is_read             │
┌─────────────────────┐       └─────────────────────┘
│ financial_records   │
├─────────────────────┤       ┌─────────────────────┐
│ id (PK)             │       │   stage_snapshots   │
│ quarter             │       ├─────────────────────┤
│ company             │       │ id (PK)             │
│ metric_id           │       │ snapshot_at         │
│ value               │       │ stage (S0-S3)       │
│ source_url          │       │ confidence          │
└─────────────────────┘       │ rationale           │
                              └─────────────────────┘
```

### 4.2 核心表 DDL

```sql
-- 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 枚举类型
CREATE TYPE sector_type AS ENUM ('B', 'C', 'A', 'D', 'E');
CREATE TYPE price_type AS ENUM ('input', 'output', 'hourly', 'monthly');
CREATE TYPE signal_type AS ENUM (
    'price_move', 'adoption_inflection', 'coverage_threshold', 
    'supply_demand_shift', 'disclosure_change', 'supply_chain_alert'
);
CREATE TYPE severity_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE stage_code AS ENUM ('S0', 'S1', 'S2', 'S3');
CREATE TYPE supply_chain_category AS ENUM ('HBM', 'DRAM', 'GPU', 'Packaging');

-- 供应商表
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    sector sector_type NOT NULL,
    pricing_page_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SKU表
CREATE TABLE skus (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    specs JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(provider_id, code)
);

-- 价格记录表 (时序表)
CREATE TABLE price_records (
    id BIGSERIAL,
    recorded_at TIMESTAMPTZ NOT NULL,
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    sku_id INTEGER NOT NULL REFERENCES skus(id),
    price_type price_type NOT NULL,
    price DECIMAL(12, 6) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    unit VARCHAR(50),
    commitment_type VARCHAR(30),
    source_url TEXT,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at)
);

-- 转换为TimescaleDB超表
SELECT create_hypertable('price_records', 'recorded_at');

-- 压缩策略 (30天后压缩)
ALTER TABLE price_records SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'provider_id, sku_id'
);
SELECT add_compression_policy('price_records', INTERVAL '30 days');

-- E板块：供应链价格表 (新增)
CREATE TABLE supply_chain_prices (
    id BIGSERIAL,
    recorded_at TIMESTAMPTZ NOT NULL,
    category supply_chain_category NOT NULL,
    item VARCHAR(50) NOT NULL,           -- 'HBM3e-24GB', 'DDR5-4800-64GB', 'H100-SXM'
    price DECIMAL(12, 4) NOT NULL,
    unit VARCHAR(30),                     -- 'USD/GB', 'USD/piece', 'percent'
    mom_change DECIMAL(6, 2),             -- 月环比变化 %
    yoy_change DECIMAL(6, 2),             -- 年同比变化 %
    source VARCHAR(50),                   -- 'TrendForce', 'DRAMeXchange', '渠道调研'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at)
);

SELECT create_hypertable('supply_chain_prices', 'recorded_at');

CREATE INDEX idx_supply_chain_category ON supply_chain_prices(category, recorded_at DESC);
CREATE INDEX idx_supply_chain_item ON supply_chain_prices(item, recorded_at DESC);

-- 信号日志表
CREATE TABLE signal_log (
    id SERIAL PRIMARY KEY,
    triggered_at TIMESTAMPTZ NOT NULL,
    signal_type signal_type NOT NULL,
    metric_id VARCHAR(10),
    provider_id INTEGER REFERENCES providers(id),
    direction VARCHAR(4),
    magnitude VARCHAR(20),
    previous_value DECIMAL(12, 6),
    current_value DECIMAL(12, 6),
    description TEXT NOT NULL,
    source_url TEXT,
    stage_implication TEXT,
    severity severity_level NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 派生指标表
CREATE TABLE derived_metrics (
    id SERIAL PRIMARY KEY,
    calculated_at TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    value DECIMAL(12, 6),
    value_low DECIMAL(12, 6),
    value_high DECIMAL(12, 6),
    company VARCHAR(10),
    period VARCHAR(10),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 阶段快照表
CREATE TABLE stage_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_at TIMESTAMPTZ NOT NULL,
    stage stage_code NOT NULL,
    confidence VARCHAR(10) NOT NULL,
    rationale TEXT NOT NULL,
    trigger_conditions JSONB NOT NULL,
    metrics_snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 财报数据表
CREATE TABLE financial_records (
    id SERIAL PRIMARY KEY,
    quarter VARCHAR(7) NOT NULL,
    company VARCHAR(10) NOT NULL,
    metric_id VARCHAR(10) NOT NULL,
    value DECIMAL(15, 2) NOT NULL,
    unit VARCHAR(30),
    yoy_change VARCHAR(20),
    qoq_change VARCHAR(20),
    source_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(quarter, company, metric_id)
);

-- 爬虫运行日志
CREATE TABLE spider_runs (
    id SERIAL PRIMARY KEY,
    spider_name VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    records_fetched INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_price_records_provider_sku ON price_records(provider_id, sku_id, recorded_at DESC);
CREATE INDEX idx_signal_log_triggered ON signal_log(triggered_at DESC);
CREATE INDEX idx_signal_log_unread ON signal_log(is_read) WHERE is_read = FALSE;
CREATE INDEX idx_derived_metrics_name ON derived_metrics(metric_name, calculated_at DESC);
```

### 4.3 初始数据

```sql
-- B板块供应商
INSERT INTO providers (code, name, sector, pricing_page_url) VALUES
('openai', 'OpenAI', 'B', 'https://platform.openai.com/docs/pricing'),
('anthropic', 'Anthropic', 'B', 'https://www.anthropic.com/pricing'),
('google', 'Google', 'B', 'https://ai.google.dev/pricing'),
('deepseek', 'DeepSeek', 'B', 'https://platform.deepseek.com/api-docs/pricing'),
('together', 'Together AI', 'B', 'https://www.together.ai/pricing');

-- C板块供应商
INSERT INTO providers (code, name, sector, pricing_page_url) VALUES
('lambda', 'Lambda Labs', 'C', 'https://lambdalabs.com/service/gpu-cloud'),
('coreweave', 'CoreWeave', 'C', 'https://www.coreweave.com/pricing'),
('runpod', 'RunPod', 'C', 'https://www.runpod.io/gpu-instance/pricing'),
('vastai', 'Vast.ai', 'C', 'https://vast.ai/');

-- E板块供应商 (供应链数据源)
INSERT INTO providers (code, name, sector, pricing_page_url) VALUES
('trendforce', 'TrendForce', 'E', 'https://www.trendforce.com/'),
('dramexchange', 'DRAMeXchange', 'E', 'https://www.dramexchange.com/'),
('skhynix', 'SK海力士', 'E', 'https://www.skhynix.com/ir/'),
('samsung_semi', '三星半导体', 'E', 'https://www.samsung.com/semiconductor/ir/'),
('micron', '美光', 'E', 'https://investors.micron.com/'),
('tsmc', '台积电', 'E', 'https://investor.tsmc.com/');

-- B板块 SKU
INSERT INTO skus (provider_id, code, name, category) VALUES
((SELECT id FROM providers WHERE code = 'openai'), 'gpt-4o', 'GPT-4o', 'flagship'),
((SELECT id FROM providers WHERE code = 'openai'), 'gpt-4o-mini', 'GPT-4o Mini', 'economy'),
((SELECT id FROM providers WHERE code = 'anthropic'), 'claude-3.5-sonnet', 'Claude 3.5 Sonnet', 'flagship'),
((SELECT id FROM providers WHERE code = 'deepseek'), 'deepseek-v3', 'DeepSeek V3', 'flagship');

-- C板块 SKU
INSERT INTO skus (provider_id, code, name, category) VALUES
((SELECT id FROM providers WHERE code = 'lambda'), 'h100-80gb', 'H100 80GB', 'gpu'),
((SELECT id FROM providers WHERE code = 'coreweave'), 'h100-80gb', 'H100 80GB', 'gpu'),
((SELECT id FROM providers WHERE code = 'runpod'), 'h100-80gb', 'H100 80GB', 'gpu');
```

---

## 五、API 接口设计

### 5.1 接口总览

| 模块 | 方法 | 路径 | 描述 |
|------|------|------|------|
| **价格** | GET | /api/v1/prices/latest | 获取最新价格 |
| | GET | /api/v1/prices/history | 获取历史价格 |
| | GET | /api/v1/prices/indices | 获取派生指数 |
| **信号** | GET | /api/v1/signals | 获取信号列表 |
| | GET | /api/v1/signals/{id} | 获取信号详情 |
| | PATCH | /api/v1/signals/{id}/read | 标记已读 |
| **阶段** | GET | /api/v1/stage/current | 获取当前阶段 |
| | GET | /api/v1/stage/history | 获取阶段历史 |
| **供应链** | GET | /api/v1/supply-chain/latest | 获取最新供应链价格 |
| | GET | /api/v1/supply-chain/history | 获取供应链价格历史 |
| | GET | /api/v1/supply-chain/tightness | 获取供应链紧张度指数 |
| **管理** | POST | /api/v1/admin/financials | 录入财报数据 |
| | POST | /api/v1/admin/supply-chain | 录入供应链数据 |
| | GET | /api/v1/admin/spider-status | 爬虫状态 |

### 5.2 接口详细规范

#### 5.2.1 获取最新价格

```
GET /api/v1/prices/latest?sector=B&category=flagship
```

**Response:**

```json
{
  "success": true,
  "data": {
    "prices": [
      {
        "id": 12345,
        "recorded_at": "2026-01-28T10:30:00Z",
        "provider": {
          "code": "openai",
          "name": "OpenAI",
          "sector": "B"
        },
        "sku": {
          "code": "gpt-4o",
          "name": "GPT-4o",
          "category": "flagship"
        },
        "price_type": "input",
        "price": 2.50,
        "currency": "USD",
        "unit": "per_million_tokens",
        "source_url": "https://platform.openai.com/docs/pricing",
        "changes": {
          "wow": -5.2,
          "mom": -12.8
        }
      }
    ],
    "updated_at": "2026-01-28T10:30:00Z"
  }
}
```

#### 5.2.2 获取价格历史

```
GET /api/v1/prices/history?provider=openai&sku=gpt-4o&start_date=2025-01-01
```

**Response:**

```json
{
  "success": true,
  "data": {
    "provider": "openai",
    "sku": "gpt-4o",
    "history": [
      {"date": "2025-03-14", "price": 30.00},
      {"date": "2025-11-01", "price": 2.50}
    ],
    "summary": {
      "start_price": 30.00,
      "end_price": 2.50,
      "total_change_pct": -91.67
    }
  }
}
```

#### 5.2.3 获取当前阶段

```
GET /api/v1/stage/current
```

**Response:**

```json
{
  "success": true,
  "data": {
    "stage": {
      "code": "S1",
      "name": "临界过渡",
      "description": "收入快速增长但仍不足，供需紧平衡"
    },
    "confidence": "MEDIUM",
    "rationale": "M01区间 0.24-0.36，A板块指标连续两季正增长",
    "determined_at": "2026-01-28T00:00:00Z",
    "key_metrics": {
      "M01": {"value_low": 0.24, "value_high": 0.36, "status": "transition"},
      "B_price_deflation_qoq": {"value": -8.2, "status": "moderate"},
      "C_spot_discount": {"value": 0.26, "status": "balanced"}
    },
    "transition_risks": {
      "to_S0": {"probability": "low", "conditions_met": 0, "conditions_total": 3},
      "to_S2": {"probability": "medium", "conditions_met": 1, "conditions_total": 2}
    }
  }
}
```

#### 5.2.4 获取信号列表

```
GET /api/v1/signals?severity=high&is_read=false&limit=20
```

**Response:**

```json
{
  "success": true,
  "data": {
    "signals": [
      {
        "id": 456,
        "triggered_at": "2026-01-27T14:30:00Z",
        "signal_type": "price_move",
        "provider": {"code": "deepseek", "name": "DeepSeek"},
        "direction": "down",
        "magnitude": "-20%",
        "description": "DeepSeek V3 输入价格下调 20%",
        "stage_implication": "S1维持，但增加S0风险",
        "severity": "high",
        "is_read": false
      }
    ]
  },
  "meta": {
    "total": 156,
    "unread_count": 3
  }
}
```

#### 5.2.5 获取派生指数

```
GET /api/v1/prices/indices
```

**Response:**

```json
{
  "success": true,
  "data": {
    "indices": [
      {
        "metric_name": "B_price_index",
        "display_name": "模型API价格指数",
        "value": 5.42,
        "unit": "USD/M tokens",
        "changes": {"wow": -3.2, "mom": -8.5, "qoq": -15.2}
      },
      {
        "metric_name": "C_rental_index",
        "display_name": "GPU租赁价格指数",
        "value": 2.58,
        "unit": "USD/hour",
        "changes": {"wow": 0.8, "mom": -2.1}
      },
      {
        "metric_name": "B_china_discount",
        "display_name": "中国厂商折扣率",
        "value": 5.6,
        "unit": "percent"
      }
    ]
  }
}
```

### 5.3 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": {"field": "start_date"}
  }
}
```

---

## 六、爬虫系统设计

### 6.1 爬虫基类

```python
# workers/spiders/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from playwright.async_api import async_playwright
import httpx


@dataclass
class PriceRecord:
    """价格记录数据类"""
    provider_code: str
    sku_code: str
    price_type: str
    price: float
    currency: str = 'USD'
    unit: Optional[str] = None
    source_url: Optional[str] = None
    recorded_at: datetime = None


class BaseSpider(ABC):
    """爬虫基类"""
    
    name: str = "base"
    provider_code: str = ""
    sector: str = ""
    
    @abstractmethod
    async def fetch(self) -> str:
        """获取页面内容"""
        pass
    
    @abstractmethod
    def parse(self, content: str) -> List[dict]:
        """解析页面内容"""
        pass
    
    def transform(self, raw_data: List[dict]) -> List[PriceRecord]:
        """转换为标准格式"""
        return [self._transform_item(item) for item in raw_data if item]
    
    @abstractmethod
    def _transform_item(self, item: dict) -> Optional[PriceRecord]:
        pass
    
    def validate(self, records: List[PriceRecord]) -> List[PriceRecord]:
        """验证数据"""
        return [r for r in records if r.price > 0 and r.sku_code]
    
    async def run(self) -> List[PriceRecord]:
        """执行爬虫"""
        content = await self.fetch()
        raw_data = self.parse(content)
        records = self.transform(raw_data)
        return self.validate(records)


class DynamicSpider(BaseSpider):
    """动态页面爬虫 (Playwright)"""
    
    url: str = ""
    wait_selector: str = ""
    
    async def fetch(self) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url, wait_until="networkidle")
            if self.wait_selector:
                await page.wait_for_selector(self.wait_selector)
            content = await page.content()
            await browser.close()
            return content


class StaticSpider(BaseSpider):
    """静态页面爬虫 (HTTP)"""
    
    url: str = ""
    
    async def fetch(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url, timeout=30.0)
            return response.text
```

### 6.2 具体爬虫示例

```python
# workers/spiders/sector_b/openai.py

import re
from bs4 import BeautifulSoup
from ..base import DynamicSpider, PriceRecord


class OpenAIPricingSpider(DynamicSpider):
    """OpenAI 定价页爬虫"""
    
    name = "openai_pricing"
    provider_code = "openai"
    sector = "B"
    url = "https://platform.openai.com/docs/pricing"
    wait_selector = "table"
    
    SKU_MAP = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
    }
    
    def parse(self, content: str) -> List[dict]:
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    model = cells[0].get_text(strip=True).lower()
                    for key, sku in self.SKU_MAP.items():
                        if key in model:
                            input_price = self._extract_price(cells[1].get_text())
                            output_price = self._extract_price(cells[2].get_text())
                            if input_price:
                                results.append({'sku': sku, 'type': 'input', 'price': input_price})
                            if output_price:
                                results.append({'sku': sku, 'type': 'output', 'price': output_price})
        return results
    
    def _extract_price(self, text: str) -> Optional[float]:
        match = re.search(r'\$?([\d.]+)\s*/?\s*(?:1M|million)', text, re.I)
        return float(match.group(1)) if match else None
    
    def _transform_item(self, item: dict) -> PriceRecord:
        return PriceRecord(
            provider_code=self.provider_code,
            sku_code=item['sku'],
            price_type=item['type'],
            price=item['price'],
            unit='per_million_tokens',
            source_url=self.url
        )
```

### 6.3 Celery 任务配置

```python
# workers/celery_app.py

from celery import Celery
from celery.schedules import crontab

app = Celery('infrawatch')

app.conf.beat_schedule = {
    # B板块：每日凌晨2点
    'crawl-sector-b-daily': {
        'task': 'workers.tasks.spider_tasks.crawl_sector_b',
        'schedule': crontab(hour=2, minute=0),
    },
    # C板块独立GPU云：每日凌晨3点
    'crawl-sector-c-indie-daily': {
        'task': 'workers.tasks.spider_tasks.crawl_sector_c_indie',
        'schedule': crontab(hour=3, minute=0),
    },
    # 派生指标计算：每日凌晨5点
    'calculate-metrics-daily': {
        'task': 'workers.tasks.metrics_tasks.calculate_all_metrics',
        'schedule': crontab(hour=5, minute=0),
    },
    # 信号检测：每日凌晨5:30
    'detect-signals-daily': {
        'task': 'workers.tasks.metrics_tasks.detect_signals',
        'schedule': crontab(hour=5, minute=30),
    },
}
```

---

## 七、核心业务逻辑

### 7.1 阶段判定引擎

```python
# app/domain/stage_engine.py

from dataclasses import dataclass
from enum import Enum
from typing import Dict
from datetime import datetime


class StageCode(str, Enum):
    S0 = "S0"  # 不可持续
    S1 = "S1"  # 临界过渡
    S2 = "S2"  # 早期自养
    S3 = "S3"  # 成熟工业化


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class StageMetrics:
    """阶段判定所需指标"""
    m01_low: float = None
    m01_high: float = None
    b_qoq_deflation: float = None
    c_spot_discount: float = None
    c_rental_qoq: float = None
    a_growth_streak: int = 0
    d3_margin_qoq: float = None


@dataclass
class StageResult:
    """阶段判定结果"""
    stage: StageCode
    confidence: Confidence
    rationale: str
    trigger_conditions: Dict[str, bool]
    transition_risks: Dict
    determined_at: datetime


class StageEngine:
    """阶段判定引擎"""
    
    THRESHOLDS = {
        'M01_CRITICAL': 0.3,
        'M01_HEALTHY': 0.7,
        'M01_SUSTAINABLE': 1.0,
        'B_DEFLATION_SEVERE': 0.15,
        'C_SPOT_EXCESS': 0.40,
        'C_RENTAL_STABLE': 0.05,
        'A_GROWTH_MIN_STREAK': 2,
    }
    
    def determine(self, metrics: StageMetrics) -> StageResult:
        """执行阶段判定"""
        
        # S0: 不可持续
        s0_conds = {
            'm01_low': metrics.m01_high and metrics.m01_high < self.THRESHOLDS['M01_CRITICAL'],
            'price_collapse': metrics.b_qoq_deflation and metrics.b_qoq_deflation > self.THRESHOLDS['B_DEFLATION_SEVERE'],
            'capacity_excess': metrics.c_spot_discount and metrics.c_spot_discount > self.THRESHOLDS['C_SPOT_EXCESS'],
        }
        
        if all(v for v in s0_conds.values() if v is not None) and sum(1 for v in s0_conds.values() if v) >= 3:
            return StageResult(
                stage=StageCode.S0,
                confidence=Confidence.HIGH,
                rationale="M01过低 + 价格崩塌 + 产能过剩",
                trigger_conditions=s0_conds,
                transition_risks={},
                determined_at=datetime.utcnow()
            )
        
        # S3: 成熟工业化
        if metrics.m01_low and metrics.m01_low > self.THRESHOLDS['M01_SUSTAINABLE']:
            return StageResult(
                stage=StageCode.S3,
                confidence=Confidence.HIGH,
                rationale="M01>1.0，实现完全自养",
                trigger_conditions={'m01_sustainable': True},
                transition_risks={},
                determined_at=datetime.utcnow()
            )
        
        # S2: 早期自养
        s2_conds = {
            'm01_healthy': metrics.m01_low and metrics.m01_low > self.THRESHOLDS['M01_HEALTHY'],
            'rental_stable': metrics.c_rental_qoq and abs(metrics.c_rental_qoq) < self.THRESHOLDS['C_RENTAL_STABLE'],
        }
        
        if all(v for v in s2_conds.values() if v is not None):
            return StageResult(
                stage=StageCode.S2,
                confidence=Confidence.HIGH,
                rationale="M01接近自养 + 供需平衡",
                trigger_conditions=s2_conds,
                transition_risks={},
                determined_at=datetime.utcnow()
            )
        
        # S1: 临界过渡 (默认)
        s1_conds = {
            'm01_transition': metrics.m01_low and self.THRESHOLDS['M01_CRITICAL'] <= metrics.m01_high <= self.THRESHOLDS['M01_HEALTHY'],
            'adoption_growing': metrics.a_growth_streak >= self.THRESHOLDS['A_GROWTH_MIN_STREAK'],
        }
        
        confidence = Confidence.HIGH if metrics.a_growth_streak >= 2 else Confidence.MEDIUM
        
        return StageResult(
            stage=StageCode.S1,
            confidence=confidence,
            rationale="M01过渡区间 或 企业采用持续增长",
            trigger_conditions=s1_conds,
            transition_risks=self._calc_transition_risks(metrics),
            determined_at=datetime.utcnow()
        )
    
    def _calc_transition_risks(self, m: StageMetrics) -> Dict:
        """计算迁移风险"""
        return {
            'to_S0': {
                'probability': 'low',
                'gap': f"需 B_deflation>{self.THRESHOLDS['B_DEFLATION_SEVERE']:.0%}"
            },
            'to_S2': {
                'probability': 'medium',
                'gap': f"需 M01>{self.THRESHOLDS['M01_HEALTHY']}, 当前差距{max(0, self.THRESHOLDS['M01_HEALTHY'] - (m.m01_low or 0)):.2f}"
            }
        }
```

### 7.2 信号检测器

```python
# app/domain/signal_detector.py

from datetime import datetime, timedelta
from typing import List
from app.models.signal import Signal, SignalType, Severity


class SignalDetector:
    """信号检测器"""
    
    THRESHOLDS = {
        'PRICE_MOVE_HIGH': 0.10,
        'PRICE_MOVE_MEDIUM': 0.05,
    }
    
    def __init__(self, price_repo, metrics_repo):
        self.price_repo = price_repo
        self.metrics_repo = metrics_repo
    
    async def detect_price_signals(self) -> List[Signal]:
        """检测价格变动信号"""
        signals = []
        current = await self.price_repo.get_latest_prices()
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        for price in current:
            prev = await self.price_repo.get_price_at(
                price.provider_id, price.sku_id, price.price_type, week_ago
            )
            
            if prev and prev.price > 0:
                change = (price.price - prev.price) / prev.price
                
                if abs(change) >= self.THRESHOLDS['PRICE_MOVE_HIGH']:
                    severity = Severity.HIGH
                elif abs(change) >= self.THRESHOLDS['PRICE_MOVE_MEDIUM']:
                    severity = Severity.MEDIUM
                else:
                    continue
                
                signals.append(Signal(
                    triggered_at=datetime.utcnow(),
                    signal_type=SignalType.PRICE_MOVE,
                    provider_id=price.provider_id,
                    direction='down' if change < 0 else 'up',
                    magnitude=f"{change:+.1%}",
                    previous_value=prev.price,
                    current_value=price.price,
                    description=f"{price.provider.name} {price.sku.name} 价格{'下跌' if change < 0 else '上涨'} {abs(change):.1%}",
                    severity=severity
                ))
        
        return signals
    
    async def detect_coverage_threshold_signals(self) -> List[Signal]:
        """检测M01跨越阈值信号"""
        signals = []
        current = await self.metrics_repo.get_latest('M01')
        previous = await self.metrics_repo.get_previous('M01')
        
        if not current or not previous:
            return signals
        
        for threshold in [0.3, 0.7, 1.0]:
            crossed_up = previous.value_low < threshold <= current.value_low
            crossed_down = previous.value_high >= threshold > current.value_high
            
            if crossed_up or crossed_down:
                signals.append(Signal(
                    triggered_at=datetime.utcnow(),
                    signal_type=SignalType.COVERAGE_THRESHOLD,
                    metric_id='M01',
                    direction='up' if crossed_up else 'down',
                    magnitude=f"crossed {threshold}",
                    description=f"M01 {'突破' if crossed_up else '跌破'} {threshold}",
                    severity=Severity.HIGH
                ))
        
        return signals
```

### 7.3 派生指标计算器

```python
# app/domain/metrics_calculator.py

from datetime import datetime
from typing import Dict, List
from app.models.derived_metric import DerivedMetric


class MetricsCalculator:
    """派生指标计算器"""
    
    # B板块价格指数权重
    B_WEIGHTS = {
        ('openai', 'gpt-4o'): 0.35,
        ('anthropic', 'claude-3.5-sonnet'): 0.30,
        ('google', 'gemini-1.5-pro'): 0.20,
        ('deepseek', 'deepseek-v3'): 0.15,
    }
    
    # C板块租赁指数权重
    C_WEIGHTS = {
        ('lambda', 'h100-80gb'): 0.30,
        ('coreweave', 'h100-80gb'): 0.30,
        ('runpod', 'h100-80gb'): 0.25,
        ('vastai', 'h100-80gb'): 0.15,
    }
    
    def __init__(self, price_repo, financial_repo):
        self.price_repo = price_repo
        self.financial_repo = financial_repo
    
    async def calculate_b_price_index(self) -> DerivedMetric:
        """计算B板块价格指数 (加权平均)"""
        prices = await self.price_repo.get_latest_prices(sector='B')
        
        total_weight = 0
        weighted_sum = 0
        
        for price in prices:
            key = (price.provider.code, price.sku.code)
            if key in self.B_WEIGHTS and price.price_type == 'input':
                weight = self.B_WEIGHTS[key]
                weighted_sum += price.price * weight
                total_weight += weight
        
        value = weighted_sum / total_weight if total_weight > 0 else 0
        
        return DerivedMetric(
            calculated_at=datetime.utcnow(),
            metric_name='B_price_index',
            value=value,
            metadata={'weights': self.B_WEIGHTS, 'components': len(prices)}
        )
    
    async def calculate_c_rental_index(self) -> DerivedMetric:
        """计算C板块租赁指数"""
        prices = await self.price_repo.get_latest_prices(sector='C')
        
        total_weight = 0
        weighted_sum = 0
        
        for price in prices:
            key = (price.provider.code, price.sku.code)
            if key in self.C_WEIGHTS:
                weight = self.C_WEIGHTS[key]
                weighted_sum += price.price * weight
                total_weight += weight
        
        value = weighted_sum / total_weight if total_weight > 0 else 0
        
        return DerivedMetric(
            calculated_at=datetime.utcnow(),
            metric_name='C_rental_index',
            value=value
        )
    
    async def calculate_china_discount(self) -> DerivedMetric:
        """计算中国厂商折扣率 (DeepSeek / OpenAI)"""
        deepseek = await self.price_repo.get_latest_price('deepseek', 'deepseek-v3', 'input')
        openai = await self.price_repo.get_latest_price('openai', 'gpt-4o', 'input')
        
        if deepseek and openai and openai.price > 0:
            ratio = (deepseek.price / openai.price) * 100
        else:
            ratio = None
        
        return DerivedMetric(
            calculated_at=datetime.utcnow(),
            metric_name='B_china_discount',
            value=ratio
        )
    
    async def calculate_m01(self, quarter: str) -> DerivedMetric:
        """计算M01覆盖率区间"""
        # 从财报数据获取
        companies = ['MSFT', 'AMZN', 'GOOGL', 'META']
        results = []
        
        for company in companies:
            ai_revenue = await self.financial_repo.get(quarter, company, 'D2')
            total_capex = await self.financial_repo.get(quarter, company, 'D1')
            
            if ai_revenue and total_capex and total_capex.value > 0:
                # AI Capex 占比假设: 40%-60%
                ai_capex_low = total_capex.value * 0.40
                ai_capex_high = total_capex.value * 0.60
                
                # 4年折旧
                depreciation_low = ai_capex_low / 4
                depreciation_high = ai_capex_high / 4
                
                # M01 = AI收入 / 折旧
                m01_low = ai_revenue.value / depreciation_high  # 分母大，结果小
                m01_high = ai_revenue.value / depreciation_low
                
                results.append({
                    'company': company,
                    'm01_low': m01_low,
                    'm01_high': m01_high
                })
        
        # 取平均
        if results:
            avg_low = sum(r['m01_low'] for r in results) / len(results)
            avg_high = sum(r['m01_high'] for r in results) / len(results)
        else:
            avg_low = avg_high = None
        
        return DerivedMetric(
            calculated_at=datetime.utcnow(),
            metric_name='M01',
            value_low=avg_low,
            value_high=avg_high,
            period=quarter,
            metadata={'companies': results}
        )
```

---

## 八、前端组件设计

### 8.1 核心组件

#### 8.1.1 阶段仪表盘组件

```tsx
// components/dashboard/StageGauge.tsx

import { useMemo } from 'react';

interface StageGaugeProps {
  stage: 'S0' | 'S1' | 'S2' | 'S3';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  rationale: string;
}

const STAGE_CONFIG = {
  S0: { name: '不可持续', color: '#ef4444', position: 12.5 },
  S1: { name: '临界过渡', color: '#f59e0b', position: 37.5 },
  S2: { name: '早期自养', color: '#84cc16', position: 62.5 },
  S3: { name: '成熟工业化', color: '#22c55e', position: 87.5 },
};

export function StageGauge({ stage, confidence, rationale }: StageGaugeProps) {
  const config = STAGE_CONFIG[stage];
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">AI 基建周期阶段</h2>
      
      {/* 仪表盘 */}
      <div className="relative h-32 mb-4">
        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full" />
        <div 
          className="absolute bottom-0 w-1 h-20 bg-gray-800 origin-bottom transform -translate-x-1/2"
          style={{ 
            left: `${config.position}%`,
            transform: `translateX(-50%) rotate(${(config.position - 50) * 1.8}deg)`
          }}
        />
      </div>
      
      {/* 阶段标签 */}
      <div className="flex justify-between text-xs text-gray-500 mb-4">
        <span>S0</span>
        <span>S1</span>
        <span>S2</span>
        <span>S3</span>
      </div>
      
      {/* 当前状态 */}
      <div className="text-center">
        <div 
          className="inline-block px-4 py-2 rounded-full text-white font-medium"
          style={{ backgroundColor: config.color }}
        >
          {stage} - {config.name}
        </div>
        <p className="mt-2 text-sm text-gray-600">
          置信度: {confidence}
        </p>
        <p className="mt-1 text-xs text-gray-500">
          {rationale}
        </p>
      </div>
    </div>
  );
}
```

#### 8.1.2 价格趋势图组件

```tsx
// components/charts/PriceTrendChart.tsx

import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PriceDataPoint {
  date: string;
  [key: string]: number | string;
}

interface PriceTrendChartProps {
  data: PriceDataPoint[];
  providers: Array<{
    key: string;
    name: string;
    color: string;
  }>;
  title?: string;
}

export function PriceTrendChart({ data, providers, title }: PriceTrendChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis 
            dataKey="date" 
            tickFormatter={(v) => new Date(v).toLocaleDateString('zh-CN', { month: 'short' })}
          />
          <YAxis 
            tickFormatter={(v) => `$${v}`}
            domain={['auto', 'auto']}
          />
          <Tooltip 
            formatter={(value: number) => [`$${value.toFixed(2)}`, '']}
            labelFormatter={(label) => new Date(label).toLocaleDateString('zh-CN')}
          />
          <Legend />
          
          {providers.map((provider) => (
            <Line
              key={provider.key}
              type="monotone"
              dataKey={provider.key}
              name={provider.name}
              stroke={provider.color}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

#### 8.1.3 信号卡片组件

```tsx
// components/signals/SignalCard.tsx

import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface Signal {
  id: number;
  triggered_at: string;
  signal_type: string;
  provider?: { name: string };
  direction: 'up' | 'down';
  magnitude: string;
  description: string;
  stage_implication?: string;
  severity: 'high' | 'medium' | 'low';
  is_read: boolean;
}

interface SignalCardProps {
  signal: Signal;
  onMarkRead: (id: number) => void;
}

const SEVERITY_STYLES = {
  high: 'border-l-red-500 bg-red-50',
  medium: 'border-l-yellow-500 bg-yellow-50',
  low: 'border-l-green-500 bg-green-50',
};

const SEVERITY_ICONS = {
  high: '🔴',
  medium: '🟡',
  low: '🟢',
};

export function SignalCard({ signal, onMarkRead }: SignalCardProps) {
  return (
    <div 
      className={`border-l-4 rounded-lg p-4 mb-3 ${SEVERITY_STYLES[signal.severity]} ${
        signal.is_read ? 'opacity-60' : ''
      }`}
    >
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2">
          <span>{SEVERITY_ICONS[signal.severity]}</span>
          <span className="text-sm text-gray-500">
            {formatDistanceToNow(new Date(signal.triggered_at), { 
              addSuffix: true, 
              locale: zhCN 
            })}
          </span>
          <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">
            {signal.signal_type}
          </span>
        </div>
        
        {!signal.is_read && (
          <button
            onClick={() => onMarkRead(signal.id)}
            className="text-xs text-blue-600 hover:underline"
          >
            标记已读
          </button>
        )}
      </div>
      
      <h4 className="font-medium mt-2">{signal.description}</h4>
      
      {signal.stage_implication && (
        <p className="text-sm text-gray-600 mt-1">
          阶段影响: {signal.stage_implication}
        </p>
      )}
      
      <div className="flex items-center gap-4 mt-2 text-sm">
        <span className={signal.direction === 'down' ? 'text-red-600' : 'text-green-600'}>
          {signal.direction === 'down' ? '↓' : '↑'} {signal.magnitude}
        </span>
        {signal.provider && (
          <span className="text-gray-500">{signal.provider.name}</span>
        )}
      </div>
    </div>
  );
}
```

#### 8.1.4 指标卡片组件

```tsx
// components/dashboard/MetricCard.tsx

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  status?: 'good' | 'warning' | 'danger' | 'neutral';
  description?: string;
}

const STATUS_COLORS = {
  good: 'text-green-600',
  warning: 'text-yellow-600',
  danger: 'text-red-600',
  neutral: 'text-gray-600',
};

export function MetricCard({ title, value, unit, change, status = 'neutral', description }: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-sm text-gray-500 mb-1">{title}</h4>
      
      <div className="flex items-baseline gap-1">
        <span className={`text-2xl font-bold ${STATUS_COLORS[status]}`}>
          {value}
        </span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
      
      {change !== undefined && (
        <div className={`text-sm mt-1 ${change < 0 ? 'text-red-500' : 'text-green-500'}`}>
          {change > 0 ? '+' : ''}{change.toFixed(1)}% 周环比
        </div>
      )}
      
      {description && (
        <p className="text-xs text-gray-400 mt-2">{description}</p>
      )}
    </div>
  );
}
```

### 8.2 API Hooks

```tsx
// lib/hooks/usePrices.ts

import useSWR from 'swr';
import { apiClient } from '../api/client';

export function useLatestPrices(sector?: string) {
  const params = new URLSearchParams();
  if (sector) params.set('sector', sector);
  
  return useSWR(
    `/api/v1/prices/latest?${params}`,
    apiClient.get,
    { refreshInterval: 60000 }  // 1分钟刷新
  );
}

export function usePriceHistory(provider: string, sku: string, days = 90) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  return useSWR(
    `/api/v1/prices/history?provider=${provider}&sku=${sku}&start_date=${startDate.toISOString()}`,
    apiClient.get
  );
}

export function usePriceIndices() {
  return useSWR('/api/v1/prices/indices', apiClient.get, {
    refreshInterval: 300000  // 5分钟刷新
  });
}


// lib/hooks/useStage.ts

import useSWR from 'swr';
import { apiClient } from '../api/client';

export function useCurrentStage() {
  return useSWR('/api/v1/stage/current', apiClient.get, {
    refreshInterval: 3600000  // 1小时刷新
  });
}


// lib/hooks/useSignals.ts

import useSWR, { mutate } from 'swr';
import { apiClient } from '../api/client';

export function useSignals(filters?: { severity?: string; is_read?: boolean }) {
  const params = new URLSearchParams();
  if (filters?.severity) params.set('severity', filters.severity);
  if (filters?.is_read !== undefined) params.set('is_read', String(filters.is_read));
  
  return useSWR(`/api/v1/signals?${params}`, apiClient.get);
}

export function useUnreadCount() {
  return useSWR('/api/v1/signals/unread-count', apiClient.get, {
    refreshInterval: 30000  // 30秒刷新
  });
}

export async function markSignalRead(id: number) {
  await apiClient.patch(`/api/v1/signals/${id}/read`);
  mutate('/api/v1/signals');
  mutate('/api/v1/signals/unread-count');
}
```

---

## 九、测试策略

### 9.1 测试金字塔

```
                    ┌───────────┐
                    │   E2E     │  10%
                    │  Tests    │
                    └─────┬─────┘
                          │
              ┌───────────┴───────────┐
              │     Integration       │  30%
              │        Tests          │
              └───────────┬───────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │            Unit Tests             │  60%
        │                                   │
        └───────────────────────────────────┘
```

### 9.2 单元测试示例

```python
# tests/unit/domain/test_stage_engine.py

import pytest
from app.domain.stage_engine import StageEngine, StageMetrics, StageCode, Confidence


class TestStageEngine:
    
    def setup_method(self):
        self.engine = StageEngine()
    
    def test_s0_all_conditions_met(self):
        """测试S0阶段判定 - 所有条件满足"""
        metrics = StageMetrics(
            m01_low=0.1,
            m01_high=0.2,
            b_qoq_deflation=0.20,  # >15%
            c_spot_discount=0.45,  # >40%
        )
        
        result = self.engine.determine(metrics)
        
        assert result.stage == StageCode.S0
        assert result.confidence == Confidence.HIGH
        assert 'M01过低' in result.rationale
    
    def test_s1_m01_in_transition(self):
        """测试S1阶段判定 - M01在过渡区间"""
        metrics = StageMetrics(
            m01_low=0.25,
            m01_high=0.45,
            b_qoq_deflation=0.08,
            c_spot_discount=0.25,
            a_growth_streak=2,
        )
        
        result = self.engine.determine(metrics)
        
        assert result.stage == StageCode.S1
        assert result.confidence == Confidence.HIGH  # a_growth_streak >= 2
    
    def test_s2_healthy_m01_and_stable_rental(self):
        """测试S2阶段判定 - M01健康且租赁价格稳定"""
        metrics = StageMetrics(
            m01_low=0.75,
            m01_high=0.85,
            c_rental_qoq=0.02,  # <5%
        )
        
        result = self.engine.determine(metrics)
        
        assert result.stage == StageCode.S2
    
    def test_s3_sustainable(self):
        """测试S3阶段判定 - 完全自养"""
        metrics = StageMetrics(
            m01_low=1.1,
            m01_high=1.3,
        )
        
        result = self.engine.determine(metrics)
        
        assert result.stage == StageCode.S3


# tests/unit/domain/test_signal_detector.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from app.domain.signal_detector import SignalDetector
from app.models.signal import SignalType, Severity


class TestSignalDetector:
    
    @pytest.fixture
    def detector(self):
        price_repo = AsyncMock()
        metrics_repo = AsyncMock()
        return SignalDetector(price_repo, metrics_repo)
    
    @pytest.mark.asyncio
    async def test_detect_high_severity_price_drop(self, detector):
        """测试检测高严重程度价格下跌"""
        # Mock当前价格
        current_price = MagicMock()
        current_price.price = 2.50
        current_price.provider_id = 1
        current_price.sku_id = 1
        current_price.price_type = 'input'
        current_price.provider = MagicMock(code='openai', name='OpenAI', sector='B')
        current_price.sku = MagicMock(name='GPT-4o')
        
        # Mock一周前价格
        previous_price = MagicMock()
        previous_price.price = 3.00  # -16.7%变化
        
        detector.price_repo.get_latest_prices.return_value = [current_price]
        detector.price_repo.get_price_at.return_value = previous_price
        
        signals = await detector.detect_price_signals()
        
        assert len(signals) == 1
        assert signals[0].severity == Severity.HIGH
        assert signals[0].direction == 'down'
    
    @pytest.mark.asyncio
    async def test_no_signal_for_small_change(self, detector):
        """测试小幅变化不产生信号"""
        current = MagicMock(price=2.50, provider_id=1, sku_id=1, price_type='input')
        previous = MagicMock(price=2.55)  # -2%变化，低于阈值
        
        detector.price_repo.get_latest_prices.return_value = [current]
        detector.price_repo.get_price_at.return_value = previous
        
        signals = await detector.detect_price_signals()
        
        assert len(signals) == 0
```

### 9.3 集成测试示例

```python
# tests/integration/test_api_prices.py

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestPricesAPI:
    
    async def test_get_latest_prices(self, async_client: AsyncClient):
        """测试获取最新价格"""
        response = await async_client.get("/api/v1/prices/latest")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'prices' in data['data']
    
    async def test_filter_by_sector(self, async_client: AsyncClient):
        """测试按板块筛选"""
        response = await async_client.get("/api/v1/prices/latest?sector=B")
        
        assert response.status_code == 200
        data = response.json()
        for price in data['data']['prices']:
            assert price['provider']['sector'] == 'B'
    
    async def test_get_price_history(self, async_client: AsyncClient):
        """测试获取价格历史"""
        response = await async_client.get(
            "/api/v1/prices/history",
            params={"provider": "openai", "sku": "gpt-4o"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'history' in data['data']
        assert 'summary' in data['data']


# tests/integration/conftest.py

import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import engine
from app.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client(setup_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

---

## 十、部署与运维

### 10.1 Docker 配置

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Playwright依赖
RUN pip install playwright && playwright install chromium --with-deps

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 默认启动API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml

version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/infrawatch
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  
  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/infrawatch
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A workers.celery_app worker --loglevel=info
  
  beat:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/infrawatch
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A workers.celery_app beat --loglevel=info
  
  db:
    image: timescale/timescaledb:latest-pg16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=infrawatch
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### 10.2 环境变量配置

```python
# app/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql://localhost/infrawatch"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # 爬虫
    SPIDER_USER_AGENT: str = "InfraWatch/1.0"
    SPIDER_TIMEOUT: int = 30
    
    # 告警
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = "alerts@infrawatch.com"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 10.3 监控指标

```python
# app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# API 指标
API_REQUESTS = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

API_LATENCY = Histogram(
    'api_request_latency_seconds',
    'API request latency',
    ['method', 'endpoint']
)

# 爬虫指标
SPIDER_RUNS = Counter(
    'spider_runs_total',
    'Total spider runs',
    ['spider_name', 'status']
)

SPIDER_RECORDS = Gauge(
    'spider_records_fetched',
    'Records fetched in last run',
    ['spider_name']
)

# 业务指标
SIGNALS_GENERATED = Counter(
    'signals_generated_total',
    'Total signals generated',
    ['signal_type', 'severity']
)

CURRENT_STAGE = Gauge(
    'current_stage',
    'Current infrastructure stage (0-3)'
)
```

### 10.4 日志配置

```python
# app/core/logging.py

import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # 降低第三方库日志级别
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
```

---

## 十一、开发规范

### 11.1 代码风格

- Python: Black + isort + flake8
- TypeScript: ESLint + Prettier
- 提交信息: Conventional Commits

### 11.2 分支策略

```
main (生产)
  │
  ├── develop (开发)
  │     │
  │     ├── feature/xxx
  │     ├── feature/yyy
  │     └── bugfix/zzz
  │
  └── hotfix/xxx (紧急修复)
```

### 11.3 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: timescale/timescaledb:latest-pg16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run linters
        run: |
          pip install black isort flake8
          black --check .
          isort --check .
          flake8 .
```

---

## 十二、附录

### 12.1 术语表

| 术语 | 定义 |
|------|------|
| Spider | 针对特定数据源的爬虫模块 |
| Hypertable | TimescaleDB的时序表 |
| Signal | 指标异动触发的事件 |
| M01 | 推理覆盖率指标 |
| Stage | 产业周期阶段 (S0-S3) |

### 12.2 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [TimescaleDB 文档](https://docs.timescale.com/)
- [Celery 文档](https://docs.celeryq.dev/)
- [Playwright 文档](https://playwright.dev/python/)
- [Next.js 文档](https://nextjs.org/docs)

### 12.3 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-01-28 | 初始版本 |

---

**文档结束**
