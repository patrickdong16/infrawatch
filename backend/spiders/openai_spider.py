"""
OpenAI 定价爬虫
从 OpenAI 官网获取模型API定价
"""

import re
import json
import logging
from typing import Any, Dict, List
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseSpider

logger = logging.getLogger(__name__)


class OpenAISpider(BaseSpider):
    """
    OpenAI 定价爬虫
    
    数据来源: https://openai.com/api/pricing/
    
    采集模型:
    - GPT-4o, GPT-4o-mini
    - GPT-4-turbo
    - o1, o1-mini, o1-pro
    - GPT-3.5-turbo
    """
    
    name = "openai_spider"
    pricing_url = "https://openai.com/api/pricing/"
    
    # 模型映射 (页面文本 -> 标准SKU ID)
    MODEL_MAPPING = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4-turbo": "gpt-4-turbo",
        "gpt-4": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "o1": "o1",
        "o1-mini": "o1-mini",
        "o1-pro": "o1-pro",
        "o3-mini": "o3-mini",
    }
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析OpenAI定价页面
        """
        results = []
        soup = BeautifulSoup(content, "html.parser")
        
        # OpenAI 的定价页面结构
        # 尝试查找价格表格或价格卡片
        
        # 方式1: 查找JSON-LD结构化数据
        json_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and "offers" in data:
                    for offer in data.get("offers", []):
                        results.append(self._parse_offer(offer))
            except json.JSONDecodeError:
                pass
        
        # 方式2: 解析HTML表格
        if not results:
            results = self._parse_html_tables(soup)
        
        # 方式3: 使用预定义的价格 (作为后备)
        if not results:
            logger.warning(f"[{self.name}] 无法从页面解析，使用预定义价格")
            results = self._get_fallback_prices()
        
        return results
    
    def _parse_html_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析HTML表格中的价格"""
        results = []
        
        # 查找包含价格的元素
        # OpenAI页面通常使用特定的CSS类
        price_elements = soup.find_all(["div", "tr", "td"], class_=re.compile(r"price|pricing|cost", re.I))
        
        for elem in price_elements:
            text = elem.get_text(strip=True)
            
            # 匹配价格模式: $0.00015 / 1K tokens
            price_match = re.search(r"\$?([\d.]+)\s*(?:\/\s*)?(?:per\s*)?(\d*[KM]?)\s*(?:tokens?|input|output)?", text, re.I)
            
            if price_match:
                price = float(price_match.group(1))
                multiplier = price_match.group(2)
                
                # 标准化为每1M tokens
                if multiplier.upper() == "K" or multiplier == "1K":
                    price = price * 1000
                elif not multiplier or multiplier == "1":
                    price = price * 1000000
                
                # 尝试匹配模型名
                model_match = re.search(r"(gpt-[34][o\-\w]*|o[13]-\w*)", text, re.I)
                if model_match:
                    model = model_match.group(1).lower()
                    results.append({
                        "sku_id": self.MODEL_MAPPING.get(model, model),
                        "price": price,
                        "currency": "USD",
                        "price_type": "input" if "input" in text.lower() else "output" if "output" in text.lower() else "default",
                        "unit": "per_million_tokens",
                    })
        
        return results
    
    def _parse_offer(self, offer: Dict) -> Dict[str, Any]:
        """解析结构化数据中的报价"""
        return {
            "sku_id": offer.get("name", "unknown"),
            "price": float(offer.get("price", 0)),
            "currency": offer.get("priceCurrency", "USD"),
            "price_type": "default",
            "unit": "per_million_tokens",
        }
    
    def _get_fallback_prices(self) -> List[Dict[str, Any]]:
        """
        后备价格数据 - 更新至 2026 精简模型列表
        
        价格单位: 每百万tokens ($/1M tokens)
        每家只保留2个代表模型
        """
        prices = [
            # GPT-4o (旗舰模型)
            {"sku_id": "gpt-4o", "price": 2.50, "price_type": "input"},
            {"sku_id": "gpt-4o", "price": 10.00, "price_type": "output"},
            # GPT-4-turbo (高性能模型)
            {"sku_id": "gpt-4-turbo", "price": 10.00, "price_type": "input"},
            {"sku_id": "gpt-4-turbo", "price": 30.00, "price_type": "output"},
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
        
        注意: OpenAI 网站有反爬机制 (403)
        生产环境建议使用 OpenAI API 或第三方数据源
        """
        # 尝试爬取，失败则使用后备数据
        target_url = url or self.pricing_url
        results = await super().run(target_url)
        
        if not results:
            logger.info(f"[{self.name}] 使用后备价格数据")
            results = self._get_fallback_prices()
        
        return results
