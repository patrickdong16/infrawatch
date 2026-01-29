"""
千问 (Qwen) 定价爬虫
从阿里云获取通义千问模型API定价
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from .base import BaseSpider

logger = logging.getLogger(__name__)


class QwenSpider(BaseSpider):
    """
    千问 (Qwen) 定价爬虫
    
    数据来源: https://help.aliyun.com/zh/model-studio/billing
    
    采集模型:
    - Qwen-Max
    - Qwen-Plus
    - Qwen-Turbo
    """
    
    name = "qwen_spider"
    pricing_url = "https://help.aliyun.com/zh/model-studio/developer-reference/tongyi-qianwen-metering-and-billing"
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析千问定价页面
        """
        logger.info(f"[{self.name}] 使用预定义价格数据")
        return self._get_fallback_prices()
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 (2025年1月价格)
        
        价格单位: 每百万tokens ($/1M tokens)
        原始价格为人民币，按1 USD = 7.2 CNY换算
        参考: 阿里云通义千问官方定价
        """
        # CNY to USD conversion rate
        CNY_TO_USD = 1 / 7.2
        
        prices = [
            # Qwen-Max (最强版本)
            {"sku_id": "qwen-max", "price": 20.0 * CNY_TO_USD, "price_type": "input", "display_name": "通义千问-Max"},
            {"sku_id": "qwen-max", "price": 60.0 * CNY_TO_USD, "price_type": "output", "display_name": "通义千问-Max"},
            # Qwen-Plus (增强版)
            {"sku_id": "qwen-plus", "price": 0.8 * CNY_TO_USD, "price_type": "input", "display_name": "通义千问-Plus"},
            {"sku_id": "qwen-plus", "price": 2.0 * CNY_TO_USD, "price_type": "output", "display_name": "通义千问-Plus"},
            # Qwen-Turbo (快速版)
            {"sku_id": "qwen-turbo", "price": 0.3 * CNY_TO_USD, "price_type": "input", "display_name": "通义千问-Turbo"},
            {"sku_id": "qwen-turbo", "price": 0.6 * CNY_TO_USD, "price_type": "output", "display_name": "通义千问-Turbo"},
            # Qwen-Long (长文本)
            {"sku_id": "qwen-long", "price": 0.5 * CNY_TO_USD, "price_type": "input", "display_name": "通义千问-Long"},
            {"sku_id": "qwen-long", "price": 2.0 * CNY_TO_USD, "price_type": "output", "display_name": "通义千问-Long"},
        ]
        
        return [
            {
                **p,
                "price": round(p["price"], 4),  # Round for cleaner display
                "currency": "USD",
                "original_currency": "CNY",
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
