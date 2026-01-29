"""
Lambda Labs 定价爬虫
从 Lambda Labs 获取 GPU 云实例定价
"""

import re
import json
import logging
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from .base import BaseSpider, APISpider

logger = logging.getLogger(__name__)


class LambdaLabsSpider(APISpider):
    """
    Lambda Labs GPU云定价爬虫
    
    数据来源: https://lambdalabs.com/service/gpu-cloud
    API: https://cloud.lambdalabs.com/api/v1/instance-types
    
    采集实例:
    - gpu_1x_h100_pcie
    - gpu_8x_h100_sxm5
    - gpu_1x_a100_sxm4
    - etc.
    """
    
    name = "lambda_labs_spider"
    api_url = "https://cloud.lambdalabs.com/api/v1/instance-types"
    pricing_page = "https://lambdalabs.com/service/gpu-cloud"
    
    async def fetch_prices(self) -> List[Dict[str, Any]]:
        """从API获取价格"""
        results = []
        
        # 尝试从API获取
        try:
            data = await self.fetch_json(self.api_url)
            if data and "data" in data:
                for instance_type, info in data["data"].items():
                    specs = info.get("instance_type", {}).get("specs", {})
                    price_cents = info.get("instance_type", {}).get("price_cents_per_hour")
                    
                    if price_cents:
                        results.append({
                            "sku_id": instance_type,
                            "price": price_cents / 100,  # 转换为美元
                            "currency": "USD",
                            "price_type": "on_demand",
                            "unit": "per_hour",
                            "specs": {
                                "gpus": specs.get("gpus"),
                                "memory_gib": specs.get("memory_gib"),
                                "vcpus": specs.get("vcpus"),
                                "storage_gib": specs.get("storage_gib"),
                            },
                            "available": info.get("regions_with_capacity_available", []),
                        })
        except Exception as e:
            logger.error(f"[{self.name}] API请求失败: {e}")
        
        # 如果API失败，使用后备数据
        if not results:
            logger.warning(f"[{self.name}] API获取失败，使用预定义价格")
            results = self._get_fallback_prices()
        
        return results
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """后备价格数据"""
        # Lambda Labs 典型价格 (2024年参考)
        instances = [
            # H100 实例
            {
                "sku_id": "gpu_1x_h100_pcie",
                "price": 2.49,
                "specs": {"gpus": 1, "gpu_type": "H100 PCIe"},
            },
            {
                "sku_id": "gpu_8x_h100_sxm5",
                "price": 23.92,
                "specs": {"gpus": 8, "gpu_type": "H100 SXM5"},
            },
            # A100 实例
            {
                "sku_id": "gpu_1x_a100_sxm4",
                "price": 1.29,
                "specs": {"gpus": 1, "gpu_type": "A100 SXM4 40GB"},
            },
            {
                "sku_id": "gpu_8x_a100_sxm4",
                "price": 10.32,
                "specs": {"gpus": 8, "gpu_type": "A100 SXM4 40GB"},
            },
            {
                "sku_id": "gpu_1x_a100_sxm4_80gb",
                "price": 1.89,
                "specs": {"gpus": 1, "gpu_type": "A100 SXM4 80GB"},
            },
            # A10 实例
            {
                "sku_id": "gpu_1x_a10",
                "price": 0.60,
                "specs": {"gpus": 1, "gpu_type": "A10"},
            },
            # RTX 实例
            {
                "sku_id": "gpu_1x_rtx6000ada",
                "price": 0.99,
                "specs": {"gpus": 1, "gpu_type": "RTX 6000 Ada"},
            },
        ]
        
        return [
            {
                **inst,
                "currency": "USD",
                "price_type": "on_demand",
                "unit": "per_hour",
                "source": "fallback",
            }
            for inst in instances
        ]
