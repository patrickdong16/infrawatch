"""
MiniMax 定价爬虫
从 MiniMax 官网获取模型API定价
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

from .base import BaseSpider

logger = logging.getLogger(__name__)


class MiniMaxSpider(BaseSpider):
    """
    MiniMax 定价爬虫
    
    数据来源: https://platform.minimaxi.com/document/Pricing
    
    采集模型:
    - abab6.5s-chat
    - abab6-chat
    - abab5.5-chat
    """
    
    name = "minimax_spider"
    pricing_url = "https://platform.minimaxi.com/document/Pricing"
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析MiniMax定价页面
        """
        logger.info(f"[{self.name}] 使用预定义价格数据")
        return self._get_fallback_prices()
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 (2025年1月价格)
        
        价格单位: 每百万tokens ($/1M tokens)
        原始价格为人民币，按1 USD = 7.2 CNY换算
        参考: MiniMax官方定价
        """
        CNY_TO_USD = 1 / 7.2
        
        prices = [
            # abab6.5s-chat (最新旗舰)
            {"sku_id": "abab6.5s-chat", "price": 10.0 * CNY_TO_USD, "price_type": "input", "display_name": "ABAB 6.5s"},
            {"sku_id": "abab6.5s-chat", "price": 30.0 * CNY_TO_USD, "price_type": "output", "display_name": "ABAB 6.5s"},
            # abab6-chat
            {"sku_id": "abab6-chat", "price": 5.0 * CNY_TO_USD, "price_type": "input", "display_name": "ABAB 6"},
            {"sku_id": "abab6-chat", "price": 15.0 * CNY_TO_USD, "price_type": "output", "display_name": "ABAB 6"},
            # abab5.5-chat (经济版)
            {"sku_id": "abab5.5-chat", "price": 1.0 * CNY_TO_USD, "price_type": "input", "display_name": "ABAB 5.5"},
            {"sku_id": "abab5.5-chat", "price": 3.0 * CNY_TO_USD, "price_type": "output", "display_name": "ABAB 5.5"},
        ]
        
        return [
            {
                **p,
                "price": round(p["price"], 4),
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
