"""
Google Cloud GPU 实例定价爬虫
从 GCP 获取 GPU VM 租赁价格
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from .base import BaseSpider

logger = logging.getLogger(__name__)


class GCPSpider(BaseSpider):
    """
    Google Cloud GPU 实例定价爬虫
    
    数据来源: https://cloud.google.com/compute/gpus-pricing
    
    采集实例:
    - a3-highgpu-8g (H100)
    - a2-highgpu-8g (A100)
    - g2-standard-96 (L4)
    """
    
    name = "gcp_spider"
    pricing_url = "https://cloud.google.com/compute/gpus-pricing"
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析GCP定价页面
        """
        logger.info(f"[{self.name}] 使用预定义价格数据")
        return self._get_fallback_prices()
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 (2025年1月 us-central1 区域价格)
        
        价格单位: $/hour
        参考: GCP Compute Engine Pricing
        """
        prices = [
            # A3 系列 (H100)
            {
                "sku_id": "a3-highgpu-8g",
                "hourly_rate": 101.22,
                "price_type": "on_demand",
                "display_name": "A3 Highgpu 8g (8x H100 80GB)",
                "gpu_type": "H100",
                "gpu_count": 8,
                "gpu_memory": 80,
            },
            # A2 系列 (A100)
            {
                "sku_id": "a2-highgpu-8g",
                "hourly_rate": 29.39,
                "price_type": "on_demand",
                "display_name": "A2 Highgpu 8g (8x A100 80GB)",
                "gpu_type": "A100",
                "gpu_count": 8,
                "gpu_memory": 80,
            },
            {
                "sku_id": "a2-highgpu-4g",
                "hourly_rate": 14.69,
                "price_type": "on_demand",
                "display_name": "A2 Highgpu 4g (4x A100 40GB)",
                "gpu_type": "A100",
                "gpu_count": 4,
                "gpu_memory": 40,
            },
            {
                "sku_id": "a2-highgpu-1g",
                "hourly_rate": 3.67,
                "price_type": "on_demand",
                "display_name": "A2 Highgpu 1g (1x A100 40GB)",
                "gpu_type": "A100",
                "gpu_count": 1,
                "gpu_memory": 40,
            },
            # G2 系列 (L4)
            {
                "sku_id": "g2-standard-96",
                "hourly_rate": 8.56,
                "price_type": "on_demand",
                "display_name": "G2 Standard 96 (8x L4)",
                "gpu_type": "L4",
                "gpu_count": 8,
                "gpu_memory": 24,
            },
            {
                "sku_id": "g2-standard-24",
                "hourly_rate": 2.14,
                "price_type": "on_demand",
                "display_name": "G2 Standard 24 (2x L4)",
                "gpu_type": "L4",
                "gpu_count": 2,
                "gpu_memory": 24,
            },
        ]
        
        return [
            {
                **p,
                "currency": "USD",
                "unit": "per_hour",
                "region": "us-central1",
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
