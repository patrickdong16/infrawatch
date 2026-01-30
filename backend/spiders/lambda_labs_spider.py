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
        # GPU 发布时间线 (用于准确的趋势计算)
        # H100: 2022-Q4 发布, 2023 云端广泛可用
        # H200: 2024-Q2 发布, 2024-Q3 云端可用
        # B100: 2024-Q3 发布, 2024-Q4 云端可用
        # B200: 2025-Q1 发布, 2025-Q2 云端可用
        
        instances = [
            # === B200 (Blackwell) - 2025 新品 ===
            {
                "sku_id": "gpu_1x_b200",
                "price": 4.99,
                "specs": {"gpus": 1, "gpu_type": "B200", "vram_gb": 192},
                "release_date": "2025-03-01",  # 2025 Q1
                "available_since": "2025-06-01",  # 云端可用
            },
            {
                "sku_id": "gpu_8x_b200",
                "price": 39.92,
                "specs": {"gpus": 8, "gpu_type": "B200", "vram_gb": 192},
                "release_date": "2025-03-01",
                "available_since": "2025-06-01",
            },
            # === B100 (Blackwell) - 2024 Q4 ===
            {
                "sku_id": "gpu_1x_b100",
                "price": 3.99,
                "specs": {"gpus": 1, "gpu_type": "B100", "vram_gb": 192},
                "release_date": "2024-09-01",
                "available_since": "2024-12-01",
            },
            {
                "sku_id": "gpu_8x_b100",
                "price": 31.92,
                "specs": {"gpus": 8, "gpu_type": "B100", "vram_gb": 192},
                "release_date": "2024-09-01",
                "available_since": "2024-12-01",
            },
            # === H200 - 2024 Q2 ===
            {
                "sku_id": "gpu_1x_h200",
                "price": 3.49,
                "specs": {"gpus": 1, "gpu_type": "H200 SXM", "vram_gb": 141},
                "release_date": "2024-03-01",
                "available_since": "2024-06-01",
            },
            {
                "sku_id": "gpu_8x_h200",
                "price": 27.92,
                "specs": {"gpus": 8, "gpu_type": "H200 SXM", "vram_gb": 141},
                "release_date": "2024-03-01",
                "available_since": "2024-06-01",
            },
            # === H100 (主流 benchmark) - 2022 Q4 ===
            {
                "sku_id": "gpu_1x_h100_pcie",
                "price": 2.49,
                "specs": {"gpus": 1, "gpu_type": "H100 PCIe", "vram_gb": 80},
                "release_date": "2022-09-01",
                "available_since": "2023-01-01",
            },
            {
                "sku_id": "gpu_8x_h100_sxm5",
                "price": 23.92,
                "specs": {"gpus": 8, "gpu_type": "H100 SXM5", "vram_gb": 80},
                "release_date": "2022-09-01",
                "available_since": "2023-01-01",
            },
            # === A100 (上一代主力) ===
            {
                "sku_id": "gpu_1x_a100_sxm4",
                "price": 1.29,
                "specs": {"gpus": 1, "gpu_type": "A100 SXM4 40GB", "vram_gb": 40},
                "release_date": "2020-05-01",
                "available_since": "2020-09-01",
            },
            {
                "sku_id": "gpu_8x_a100_sxm4",
                "price": 10.32,
                "specs": {"gpus": 8, "gpu_type": "A100 SXM4 40GB", "vram_gb": 40},
                "release_date": "2020-05-01",
                "available_since": "2020-09-01",
            },
            {
                "sku_id": "gpu_1x_a100_sxm4_80gb",
                "price": 1.89,
                "specs": {"gpus": 1, "gpu_type": "A100 SXM4 80GB", "vram_gb": 80},
                "release_date": "2020-11-01",
                "available_since": "2021-03-01",
            },
            # === 中低端 GPU ===
            {
                "sku_id": "gpu_1x_a10",
                "price": 0.60,
                "specs": {"gpus": 1, "gpu_type": "A10", "vram_gb": 24},
                "release_date": "2021-04-01",
                "available_since": "2021-06-01",
            },
            {
                "sku_id": "gpu_1x_rtx6000ada",
                "price": 0.99,
                "specs": {"gpus": 1, "gpu_type": "RTX 6000 Ada", "vram_gb": 48},
                "release_date": "2022-12-01",
                "available_since": "2023-03-01",
            },
            {
                "sku_id": "gpu_1x_l40s",
                "price": 1.19,
                "specs": {"gpus": 1, "gpu_type": "L40S", "vram_gb": 48},
                "release_date": "2023-08-01",
                "available_since": "2023-11-01",
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

