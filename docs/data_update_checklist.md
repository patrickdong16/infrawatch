# InfraWatch 数据更新清单

## 当前状态
- **最新数据**: 2025-Q1
- **当前时间**: 2026-Q1
- **缺失**: 2025-Q2, Q3, Q4, 2026-Q1

---

## 📊 需要更新的数据类型

### 1. GPU 云端价格 (`gpu_efficiency.yml`)

| 数据源 | URL | 更新频率 |
|--------|-----|----------|
| Lambda Labs | https://lambdalabs.com/service/gpu-cloud | 实时 |
| CoreWeave | https://www.coreweave.com/pricing | 实时 |
| RunPod | https://www.runpod.io/gpu-instance/pricing | 实时 |
| AWS (p5/p4d) | https://aws.amazon.com/ec2/instance-types/p5/ | 季度 |
| Azure (ND H100) | https://azure.microsoft.com/pricing/details/virtual-machines/ | 季度 |
| GCP (A3) | https://cloud.google.com/compute/gpus-pricing | 季度 |

**采集字段**: GPU型号, 每小时价格, 内存配置

---

### 2. 推理覆盖率 (`inference_coverage.yml`)

| 公司 | 数据来源 | 估算方法 |
|------|----------|----------|
| **OpenAI** | 公开报道 + 融资估值 | ARR估算 ÷ GPU资产折旧 |
| **Anthropic** | 融资报道 | 营收估算 ÷ |
| **Microsoft** | 季度财报 (Azure AI段) | AI服务收入 ÷ CapEx分摊 |
| **Google** | 季度财报 (Cloud AI) | Vertex收入 ÷ TPU资产 |
| **AWS** | 季度财报 (AWS AI) | Bedrock收入估算 |

**关键报道来源**:
- The Information, Bloomberg, WSJ 科技版
- 公司季度财报电话会议
- Semianalysis 行业分析

---

### 3. CapEx 资本密集度

| 公司 | 财报页面 |
|------|----------|
| Microsoft | https://www.microsoft.com/investor/reports |
| Google | https://abc.xyz/investor/ |
| Amazon | https://ir.aboutamazon.com/quarterly-results |
| Meta | https://investor.fb.com/financials/ |

**提取字段**: CapEx (TTM), 总营收, AI相关 CapEx 占比 (如有披露)

---

## 🔧 建议实现方式

### 短期 (手动)
1. 定期(每季度)手动更新 YAML 配置文件
2. 建立来源 checklist 确保一致性

### 中期 (半自动)
1. 创建 `scripts/update_quarterly_data.py`
2. 从财报 PDF 或公开 API 拉取数据
3. 生成待审核的 YAML 更新

### 长期 (自动化)
1. 爬虫自动采集 GPU 价格 (已有 Spiders)
2. 财报日历提醒 + LLM 辅助提取
3. 数据库存储替代静态 YAML

---

## ✅ 下一步行动

- [ ] 收集 2025-Q2/Q3/Q4 GPU 价格历史
- [ ] 收集 2025 年 OpenAI/Anthropic 营收报道
- [ ] 收集 2025 年云厂商财报 CapEx 数据
- [ ] 更新 `gpu_efficiency.yml`
- [ ] 更新 `inference_coverage.yml`
