"""
Azure GPU 实例定价爬虫
从 Azure 获取 GPU VM 租赁价格
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from .base import BaseSpider

logger = logging.getLogger(__name__)


class AzureSpider(BaseSpider):
    """
    Azure GPU VM 定价爬虫
    
    数据来源: https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/
    
    采集实例:
    - ND96asr_v4 (A100)
    - ND96amsr_A100_v4 (A100 80GB)
    - NC24ads_A100_v4 (A100)
    - NV72ads_A10_v5 (A10)
    """
    
    name = "azure_spider"
    pricing_url = "https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/"
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析Azure定价页面
        """
        logger.info(f"[{self.name}] 使用预定义价格数据")
        return self._get_fallback_prices()
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 (2025年1月 East US 区域价格)
        
        价格单位: $/hour
        参考: Azure VM Pricing
        """
        prices = [
            # ND 系列 (A100)
            {
                "sku_id": "nd96asr-v4",
                "hourly_rate": 27.20,
                "price_type": "on_demand",
                "display_name": "ND96asr_v4 (8x A100 40GB)",
                "gpu_type": "A100",
                "gpu_count": 8,
                "gpu_memory": 40,
            },
            {
                "sku_id": "nd96amsr-a100-v4",
                "hourly_rate": 32.77,
                "price_type": "on_demand",
                "display_name": "ND96amsr_A100_v4 (8x A100 80GB)",
                "gpu_type": "A100",
                "gpu_count": 8,
                "gpu_memory": 80,
            },
            # NC 系列 (A100 单卡)
            {
                "sku_id": "nc24ads-a100-v4",
                "hourly_rate": 3.67,
                "price_type": "on_demand",
                "display_name": "NC24ads_A100_v4 (1x A100 80GB)",
                "gpu_type": "A100",
                "gpu_count": 1,
                "gpu_memory": 80,
            },
            # NV 系列 (A10)
            {
                "sku_id": "nv72ads-a10-v5",
                "hourly_rate": 5.54,
                "price_type": "on_demand",
                "display_name": "NV72ads_A10_v5 (2x A10)",
                "gpu_type": "A10",
                "gpu_count": 2,
                "gpu_memory": 24,
            },
            # NCads H100 v5 (H100)
            {
                "sku_id": "nc40ads-h100-v5",
                "hourly_rate": 8.97,
                "price_type": "on_demand",
                "display_name": "NC40ads_H100_v5 (1x H100 80GB)",
                "gpu_type": "H100",
                "gpu_count": 1,
                "gpu_memory": 80,
            },
        ]
        
        return [
            {
                **p,
                "currency": "USD",
                "unit": "per_hour",
                "region": "eastus",
                "source": "fallback",
                "recorded_at": datetime.utcnow().isoformat(),
            }
            for p in prices
        ]
    
    async def run(self, url: str = None) -> List[Dict[str, Any]]:
        """执行爬虫"""
        target_url = url or self.pricing_url
        results = await super().run(target_url)
        
        if not results:
            logger.info(f"[{self.name}] 使用后备价格数据")
            results = self._get_fallback_prices()
        
        return results
