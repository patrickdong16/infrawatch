"""
Anthropic 定价爬虫
从 Anthropic 官网获取 Claude 模型API定价
"""

import re
import json
import logging
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from .base import BaseSpider

logger = logging.getLogger(__name__)


class AnthropicSpider(BaseSpider):
    """
    Anthropic 定价爬虫
    
    数据来源: https://www.anthropic.com/pricing
    
    采集模型:
    - Claude 3.5 Sonnet
    - Claude 3.5 Haiku
    - Claude 3 Opus
    """
    
    name = "anthropic_spider"
    pricing_url = "https://www.anthropic.com/pricing"
    
    # 模型映射
    MODEL_MAPPING = {
        "claude-3.5-sonnet": "claude-3-5-sonnet",
        "claude-3-5-sonnet": "claude-3-5-sonnet",
        "claude-3.5-haiku": "claude-3-5-haiku",
        "claude-3-5-haiku": "claude-3-5-haiku",
        "claude-3-opus": "claude-3-opus",
        "claude-3-sonnet": "claude-3-sonnet",
        "claude-3-haiku": "claude-3-haiku",
    }
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析Anthropic定价页面"""
        results = []
        soup = BeautifulSoup(content, "html.parser")
        
        # 尝试解析表格结构
        results = self._parse_pricing_cards(soup)
        
        # 后备数据
        if not results:
            logger.warning(f"[{self.name}] 无法从页面解析，使用预定义价格")
            results = self._get_fallback_prices()
        
        return results
    
    def _parse_pricing_cards(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析定价卡片"""
        results = []
        
        # Anthropic 页面结构
        # 查找包含模型名和价格的元素
        cards = soup.find_all(["div", "article", "section"], class_=re.compile(r"card|pricing|model", re.I))
        
        for card in cards:
            text = card.get_text(" ", strip=True)
            
            # 匹配 Claude 模型
            model_match = re.search(r"(claude[- ]3\.?5?[- ]?\w+)", text, re.I)
            if not model_match:
                continue
            
            model = model_match.group(1).lower().replace(" ", "-").replace(".", "-")
            
            # 匹配价格
            # 格式: $3 / MTok (input) 或 $15 / MTok (output)
            price_matches = re.findall(r"\$?([\d.]+)\s*(?:\/\s*)?(?:MTok|million|M\s*tokens?)\s*(?:\(?(input|output)\)?)?", text, re.I)
            
            for price_str, price_type in price_matches:
                try:
                    price = float(price_str)
                    results.append({
                        "sku_id": self.MODEL_MAPPING.get(model, model),
                        "price": price,
                        "currency": "USD",
                        "price_type": price_type.lower() if price_type else "default",
                        "unit": "per_million_tokens",
                    })
                except ValueError:
                    pass
        
        return results
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """后备价格数据 - 更新至 2026 最新模型"""
        prices = [
            # Claude Sonnet 4 (2026)
            {"sku_id": "claude-sonnet-4", "price": 3.00, "price_type": "input"},
            {"sku_id": "claude-sonnet-4", "price": 15.00, "price_type": "output"},
            # Claude Opus 4.5 (2026)
            {"sku_id": "claude-opus-4.5", "price": 15.00, "price_type": "input"},
            {"sku_id": "claude-opus-4.5", "price": 75.00, "price_type": "output"},
        ]
        
        return [
            {
                **p,
                "currency": "USD",
                "unit": "per_million_tokens",
                "source": "fallback",
            }
            for p in prices
        ]
    
    async def run(self, url: str = None) -> List[Dict[str, Any]]:
        """
        执行爬虫
        
        注意: Anthropic 网站重定向 (301)
        生产环境建议使用 Anthropic API 或第三方数据源
        """
        results = await super().run(url or self.pricing_url)
        
        if not results:
            logger.info(f"[{self.name}] 使用后备价格数据")
            results = self._get_fallback_prices()
        
        return results
