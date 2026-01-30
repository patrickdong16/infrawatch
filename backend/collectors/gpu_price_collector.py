"""
GPU 价格历史采集器
从多个云服务商聚合 GPU 价格并存储历史记录
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 导入现有爬虫
from spiders.lambda_labs_spider import LambdaLabsSpider
from spiders.aws_spider import AWSSpider
from spiders.azure_spider import AzureSpider
from spiders.gcp_spider import GCPSpider

logger = logging.getLogger(__name__)

# 历史数据存储路径
DATA_DIR = Path(__file__).parent.parent / "data" / "gpu_prices"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class GPUPriceCollector:
    """
    GPU 价格聚合采集器
    
    功能:
    1. 从多个云服务商采集实时价格
    2. 存储历史价格快照
    3. 更新 gpu_efficiency.yml 配置
    """
    
    PROVIDERS = {
        "lambda_labs": LambdaLabsSpider,
        "aws": AWSSpider,
        "azure": AzureSpider,
        "gcp": GCPSpider,
    }
    
    # H100 SKU 标准化映射
    H100_SKU_PATTERNS = {
        "h100_sxm": ["h100_sxm", "h100-sxm", "gpu_1x_h100", "p5.48xlarge"],
        "h100_pcie": ["h100_pcie", "h100-pcie", "Standard_NC96ads_H100"],
        "h200": ["h200", "gpu_1x_h200"],
        "a100_80gb": ["a100_80gb", "a100-80gb", "gpu_1x_a100_sxm4_80gb"],
    }
    
    async def collect_all(self) -> Dict[str, List[Dict]]:
        """从所有服务商采集价格"""
        results = {}
        
        for provider_name, spider_class in self.PROVIDERS.items():
            try:
                spider = spider_class()
                prices = await spider.run()
                results[provider_name] = prices
                logger.info(f"[{provider_name}] 采集到 {len(prices)} 条价格")
            except Exception as e:
                logger.error(f"[{provider_name}] 采集失败: {e}")
                results[provider_name] = []
        
        return results
    
    def normalize_gpu_type(self, sku_id: str) -> str:
        """将 SKU ID 标准化为 GPU 类型"""
        sku_lower = sku_id.lower()
        for gpu_type, patterns in self.H100_SKU_PATTERNS.items():
            if any(p in sku_lower for p in patterns):
                return gpu_type
        return sku_id
    
    def aggregate_h100_prices(self, all_prices: Dict[str, List[Dict]]) -> Dict[str, float]:
        """聚合 H100 等关键 GPU 的最低价格"""
        gpu_prices = {}
        
        for provider, prices in all_prices.items():
            for price in prices:
                gpu_type = self.normalize_gpu_type(price.get("sku_id", ""))
                hourly_price = price.get("price", 0)
                
                if gpu_type in ["h100_sxm", "h100_pcie", "h200", "a100_80gb"]:
                    key = f"{gpu_type}"
                    # 保存每小时最低价
                    if price.get("unit") == "per_hour":
                        if key not in gpu_prices or hourly_price < gpu_prices[key]:
                            gpu_prices[key] = hourly_price
        
        return gpu_prices
    
    def save_snapshot(self, provider_prices: Dict[str, List[Dict]]) -> str:
        """保存价格快照"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = DATA_DIR / f"prices_{timestamp}.json"
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "providers": provider_prices,
            "aggregated": self.aggregate_h100_prices(provider_prices),
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        logger.info(f"价格快照已保存: {filename}")
        return str(filename)
    
    def get_current_quarter(self) -> str:
        """获取当前季度标识"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"
    
    async def run(self) -> Dict[str, Any]:
        """执行采集并保存"""
        logger.info("开始 GPU 价格采集...")
        
        # 采集所有服务商价格
        all_prices = await self.collect_all()
        
        # 保存快照
        snapshot_file = self.save_snapshot(all_prices)
        
        # 聚合关键 GPU 价格
        aggregated = self.aggregate_h100_prices(all_prices)
        
        return {
            "quarter": self.get_current_quarter(),
            "snapshot_file": snapshot_file,
            "aggregated_prices": aggregated,
            "total_records": sum(len(p) for p in all_prices.values()),
        }


async def main():
    """CLI 入口"""
    logging.basicConfig(level=logging.INFO)
    collector = GPUPriceCollector()
    result = await collector.run()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
