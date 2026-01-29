"""
AWS GPU 实例定价爬虫
从 AWS 获取 GPU 实例租赁价格
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from .base import BaseSpider

logger = logging.getLogger(__name__)


class AWSSpider(BaseSpider):
    """
    AWS GPU 实例定价爬虫
    
    数据来源: https://aws.amazon.com/ec2/pricing/on-demand/
    
    采集实例:
    - p5.48xlarge (H100)
    - p4d.24xlarge (A100)
    - inf2.48xlarge (Inferentia2)
    - trn1.32xlarge (Trainium)
    """
    
    name = "aws_spider"
    pricing_url = "https://aws.amazon.com/ec2/pricing/on-demand/"
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析AWS定价页面
        """
        logger.info(f"[{self.name}] 使用预定义价格数据")
        return self._get_fallback_prices()
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 (2025年1月 us-east-1 区域价格)
        
        价格单位: $/hour
        参考: AWS EC2 On-Demand Pricing
        """
        prices = [
            # P5 系列 (H100)
            {
                "sku_id": "p5.48xlarge",
                "hourly_rate": 98.32,
                "price_type": "on_demand",
                "display_name": "P5.48xlarge (8x H100)",
                "gpu_type": "H100",
                "gpu_count": 8,
                "gpu_memory": 80,
            },
            # P4d 系列 (A100)
            {
                "sku_id": "p4d.24xlarge",
                "hourly_rate": 32.77,
                "price_type": "on_demand",
                "display_name": "P4d.24xlarge (8x A100)",
                "gpu_type": "A100",
                "gpu_count": 8,
                "gpu_memory": 40,
            },
            # Inf2 系列 (Inferentia2)
            {
                "sku_id": "inf2.48xlarge",
                "hourly_rate": 12.98,
                "price_type": "on_demand",
                "display_name": "Inf2.48xlarge (12x Inferentia2)",
                "gpu_type": "Inferentia2",
                "gpu_count": 12,
            },
            # Trn1 系列 (Trainium)
            {
                "sku_id": "trn1.32xlarge",
                "hourly_rate": 21.50,
                "price_type": "on_demand",
                "display_name": "Trn1.32xlarge (16x Trainium)",
                "gpu_type": "Trainium",
                "gpu_count": 16,
            },
            # G5 系列 (A10G) - 推理优化
            {
                "sku_id": "g5.48xlarge",
                "hourly_rate": 16.29,
                "price_type": "on_demand",
                "display_name": "G5.48xlarge (8x A10G)",
                "gpu_type": "A10G",
                "gpu_count": 8,
                "gpu_memory": 24,
            },
        ]
        
        return [
            {
                **p,
                "currency": "USD",
                "unit": "per_hour",
                "region": "us-east-1",
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
