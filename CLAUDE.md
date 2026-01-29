# InfraWatch - Claude 开发规范

> **项目代号**: InfraWatch  
> **版本**: v1.0  
> **日期**: 2026-01-29

---

## 🚨 最高优先级：强制参照 REQUIREMENTS.md

> [!CAUTION]
> **在进行任何开发工作之前，必须先阅读 [REQUIREMENTS.md](./REQUIREMENTS.md)**
> 
> 这是本项目的需求规格说明书，包含：
> - 监测体系架构 (A/B/C/D/E五大板块)
> - 阶段判定规则 (S0-S3四阶段模型)
> - 技术规格 (技术栈、项目结构、API规范)
> - 验收标准

**如果 REQUIREMENTS.md 中有明确规定，必须严格遵循，不得自行发挥。**

---

## 一、项目概述

InfraWatch 是一个 **AI基建可持续性监测平台**，核心功能：
1. 追踪模型API价格 (B板块) 和 GPU租赁价格 (C板块)
2. 计算派生指标 (价格指数、M01覆盖率)
3. 判定产业周期阶段 (S0-S3)
4. 触发并推送信号 (价格异动、阶段变化)

---

## 二、核心业务规则

### 2.1 绝对禁止事项

| 禁止项 | 原因 |
|--------|------|
| ❌ 预测未来价格/阶段 | 系统只记录已发生的变化 |
| ❌ 自动判定阶段变化 | 系统输出信号，人工确认阶段 |
| ❌ 硬编码API密钥 | 使用环境变量 |
| ❌ 虚构数据源URL | 必须使用真实可访问的链接 |

### 2.2 M01 计算规则

```python
# M01 = AI推理收入 / AI相关资产年化折旧
# AI Capex占比假设: 40%-60%
# 折旧周期: 4年

ai_capex_low = total_capex * 0.40
ai_capex_high = total_capex * 0.60
depreciation_low = ai_capex_low / 4
depreciation_high = ai_capex_high / 4
m01_low = ai_revenue / depreciation_high
m01_high = ai_revenue / depreciation_low
```

### 2.3 阶段判定规则 (来自 REQUIREMENTS.md)

| 阶段 | 触发条件 |
|------|----------|
| S0 | M01_high < 0.3 且 B_qoq_deflation > 15% 且 C_spot_discount > 40% |
| S1 | M01 在 0.3-0.7 区间 或 A板块指标连续两季正增长 |
| S2 | M01_low > 0.7 且 C_rental_index 环比 < ±5% |
| S3 | M01_low > 1.0 且 D3 云利润率稳定 |

---

## 三、技术规范

### 3.1 技术栈 (强制)

| 层级 | 选型 | 备注 |
|------|------|------|
| 后端 | FastAPI + SQLAlchemy 2.x | 异步优先 |
| 前端 | Next.js 14 + Tailwind + shadcn/ui | App Router |
| 数据库 | PostgreSQL + TimescaleDB | 时序数据优化 |
| 爬虫 | Playwright | 支持JS渲染 |
| 任务队列 | Celery + Redis | 定时任务 |

### 3.2 项目结构 (强制)

```
infrawatch/
├── CLAUDE.md              # 本文件
├── REQUIREMENTS.md        # 需求规格说明书 ⚠️ 必读
├── docs/                  # 原始技术文档
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/       # REST API
│   │   ├── domain/       # 业务逻辑 (stage_engine, signal_detector)
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic 模型
│   │   └── services/     # 服务层
│   └── workers/
│       ├── spiders/      # 爬虫
│       └── tasks/        # Celery 任务
└── frontend/              # Next.js 前端
    ├── app/              # 页面
    └── components/       # 组件
```

### 3.3 API 响应格式 (强制)

```python
# 成功响应
{"success": True, "data": {...}}

# 错误响应
{"success": False, "error": {"code": "...", "message": "...", "details": {...}}}
```

### 3.4 数据库命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 表名 | 小写下划线复数 | `price_records`, `signal_log` |
| 字段名 | 小写下划线 | `recorded_at`, `provider_id` |
| 枚举类型 | 小写下划线 | `sector_type`, `price_type` |

---

## 四、开发工作流

### 4.1 编码前必须确认

- [ ] 阅读 REQUIREMENTS.md 相关章节
- [ ] 确认当前工作属于哪个模块 (P1-P7)
- [ ] 确认数据板块 (A/B/C/D/E)
- [ ] 确认环境变量配置

### 4.2 爬虫开发规范

```python
# 爬虫基类继承
class XXXSpider(BaseSpider):
    name = "xxx_pricing"          # 爬虫名称
    provider_code = "xxx"         # 供应商代码 (providers表)
    sector = "B"                  # 板块: B/C/E
    url = "https://..."           # 目标URL
    
    async def fetch(self) -> str: ...
    def parse(self, content: str) -> List[dict]: ...
    def _transform_item(self, item: dict) -> PriceRecord: ...
```

### 4.3 信号触发阈值

| 信号类型 | 严重程度 | 阈值 |
|----------|----------|------|
| price_move | HIGH | 周环比 > 10% |
| price_move | MEDIUM | 周环比 5-10% |
| adoption_inflection | MEDIUM | 季度环比 > 20% |
| coverage_threshold | HIGH | M01跨越0.3/0.7/1.0 |

---

## 五、环境变量

```bash
# .env.example - 必须维护此文件

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/infrawatch

# Redis
REDIS_URL=redis://localhost:6379/0

# 前端
NEXT_PUBLIC_API_URL=http://localhost:8000

# 可选: 爬虫代理
PROXY_URL=
```

---

## 六、测试要求

### 6.1 单元测试覆盖

| 模块 | 最低覆盖率 |
|------|------------|
| domain/ (业务逻辑) | 80% |
| spiders/ (爬虫解析) | 70% |
| api/ (接口) | 60% |

### 6.2 测试命名规范

```python
# test_<module>_<scenario>.py
def test_stage_engine_s0_trigger():
    """当M01<0.3且价格崩塌时应判定为S0"""
    ...

def test_signal_detector_price_move_high():
    """周环比>10%应触发高严重度信号"""
    ...
```

---

## 七、部署清单

- [ ] 确认环境变量已设置
- [ ] 数据库迁移已执行
- [ ] 初始数据 (providers, skus) 已导入
- [ ] Celery Worker 已启动
- [ ] Celery Beat 已启动 (定时任务)
- [ ] 爬虫首次运行成功

---

## 八、常见问题

### Q: 价格单位如何标准化？
A: 统一使用 `USD`，模型API价格单位为 `per_million_tokens`，GPU租赁为 `per_hour`

### Q: 如何处理爬虫失败？
A: 
1. 记录到 `spider_runs` 表
2. 触发 `disclosure_change` 信号 (如果连续失败)
3. 不自动重试，等待下次调度

### Q: M01计算时缺少某些财报数据？
A: 使用已有数据计算，在 `metadata` 中记录缺失项，不做估算

---

## 九、文档索引

| 文档 | 位置 | 用途 |
|------|------|------|
| **REQUIREMENTS.md** | ./REQUIREMENTS.md | ⚠️ 需求规格说明书 (必读) |
| 监测体系 v2.1 | ./docs/AI_基建可持续拐点监测体系_v2.1.md | 方法论 |
| PRD | ./docs/AI_Infra_Monitor_PRD.md | 产品设计 |
| TDD | ./docs/AI_Infra_Monitor_TDD.md | 技术设计 |

---

*本文档对本项目所有开发工作生效，Claude 必须严格遵守*
