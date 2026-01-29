"""
DeepSeek 定价爬虫
从 DeepSeek 官网获取模型API定价
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from .base import BaseSpider

logger = logging.getLogger(__name__)


class DeepSeekSpider(BaseSpider):
    """
    DeepSeek 定价爬虫
    
    数据来源: https://platform.deepseek.com/api-docs/pricing
    
    采集模型:
    - DeepSeek-V3
    - DeepSeek-R1
    - DeepSeek-Chat
    """
    
    name = "deepseek_spider"
    pricing_url = "https://platform.deepseek.com/api-docs/pricing"
    
    # 模型映射
    MODEL_MAPPING = {
        "deepseek-chat": "deepseek-v3",
        "deepseek-reasoner": "deepseek-r1",
    }
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析DeepSeek定价页面
        """
        # DeepSeek 页面通常需要 JS 渲染，使用后备数据
        logger.info(f"[{self.name}] 使用预定义价格数据")
        return self._get_fallback_prices()
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 (2025年1月价格)
        
        价格单位: 每百万tokens ($/1M tokens)
        参考: https://api-docs.deepseek.com/quick_start/pricing
        """
        prices = [
            # DeepSeek-V3 (deepseek-chat)
            {"sku_id": "deepseek-v3", "price": 0.27, "price_type": "input", "display_name": "DeepSeek-V3"},
            {"sku_id": "deepseek-v3", "price": 1.10, "price_type": "output", "display_name": "DeepSeek-V3"},
            # DeepSeek-R1 (deepseek-reasoner)
            {"sku_id": "deepseek-r1", "price": 0.55, "price_type": "input", "display_name": "DeepSeek-R1"},
            {"sku_id": "deepseek-r1", "price": 2.19, "price_type": "output", "display_name": "DeepSeek-R1"},
            # DeepSeek-Chat (legacy)
            {"sku_id": "deepseek-chat", "price": 0.14, "price_type": "input", "display_name": "DeepSeek-Chat"},
            {"sku_id": "deepseek-chat", "price": 0.28, "price_type": "output", "display_name": "DeepSeek-Chat"},
        ]
        
        return [
            {
                **p,
                "currency": "USD",
                "unit": "per_million_tokens",
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
