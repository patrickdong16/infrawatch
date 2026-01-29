# InfraWatch - AI 基建可持续性监测平台

追踪 AI 基础设施价格信号，识别产业周期拐点。

## 功能特性

- **价格监测中心**: 追踪 B板块(模型API定价) 和 C板块(GPU租赁价格)
- **供应链监测**: 追踪 E板块(HBM/DRAM/GPU ASP/CoWoS产能)
- **阶段仪表盘**: 四阶段模型(S0-S3)判定当前周期位置
- **信号中心**: 自动检测价格异动、采用拐点、供应链预警
- **M01覆盖率分析**: 计算推理收入覆盖折旧的能力

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL + TimescaleDB
- **任务队列**: Celery + Redis
- **爬虫**: Playwright + BeautifulSoup

### 前端
- **框架**: Next.js 14
- **样式**: Tailwind CSS
- **图表**: Recharts
- **状态管理**: SWR

## 快速开始

### 使用 Docker Compose (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 初始化数据库
docker-compose exec api python scripts/seed_data.py

# 访问
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
alembic upgrade head

# 初始化种子数据
python scripts/seed_data.py

# 启动 API 服务
uvicorn app.main:app --reload

# 启动 Celery Worker (新终端)
celery -A workers.celery_app worker --loglevel=info

# 启动 Celery Beat (新终端)
celery -A workers.celery_app beat --loglevel=info
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

## 项目结构

```
infrawatch/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 路由
│   │   ├── core/            # 核心模块 (数据库, 配置)
│   │   ├── domain/          # 业务逻辑 (阶段引擎, 信号检测)
│   │   ├── models/          # 数据库模型
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # 业务服务
│   ├── workers/
│   │   ├── spiders/         # 爬虫模块
│   │   └── tasks/           # Celery 任务
│   └── scripts/             # 脚本
├── frontend/
│   ├── app/                 # Next.js 页面
│   ├── components/          # React 组件
│   ├── lib/                 # 工具库
│   └── types/               # TypeScript 类型
└── docker-compose.yml
```

## API 文档

启动后端后访问: http://localhost:8000/docs

主要接口:
- `GET /api/v1/prices/latest` - 获取最新价格
- `GET /api/v1/prices/history` - 获取价格历史
- `GET /api/v1/signals` - 获取信号列表
- `GET /api/v1/stage/current` - 获取当前阶段
- `GET /api/v1/supply-chain/latest` - 获取供应链价格

## 监测体系说明

### 板块定义

| 板块 | 名称 | 数据内容 |
|------|------|----------|
| A | 企业应用采用 | Copilot坐席数、ServiceNow Pro Plus渗透率 |
| B | 模型API定价 | OpenAI、Anthropic、DeepSeek等价格 |
| C | GPU租赁价格 | Lambda、CoreWeave、RunPod等价格 |
| D | 巨头财务数据 | Capex、AI收入、云利润率 |
| E | 供应链价格 | HBM、DRAM、GPU ASP、CoWoS产能 |

### 阶段定义

| 阶段 | 名称 | 特征 |
|------|------|------|
| S0 | 不可持续 | M01<0.3, 价格崩塌, 产能过剩 |
| S1 | 临界过渡 | M01在0.3-0.7, 快速增长 |
| S2 | 早期自养 | M01>0.7, 价格稳定 |
| S3 | 成熟工业化 | M01>1.0, 完全自养 |

## 配置说明

### 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/infrawatch

# Redis
REDIS_URL=redis://localhost:6379/0

# API
CORS_ORIGINS=["http://localhost:3000"]

# 爬虫
SPIDER_USER_AGENT=InfraWatch/1.0
SPIDER_TIMEOUT=30
```

## License

MIT
