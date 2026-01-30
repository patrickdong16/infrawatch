# TrendForce 存储价格爬虫计划

## 目标
自动追踪 HBM/DRAM 价格信号

## 历史数据获取
- 新闻方式: 只能追踪未来数据
- 历史数据: 需从 Google News 搜索旧报道 + AI 批量提取

## 新增文件

1. `spiders/trendforce_spider.py` - 抓取 DRAMeXchange 新闻
2. `config/supply_chain.yml` - 添加历史数据点
3. `scripts/seed_historical_prices.py` - 批量导入
