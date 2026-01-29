"""
爬虫包
"""

from .base import BaseSpider, APISpider
from .openai_spider import OpenAISpider
from .anthropic_spider import AnthropicSpider
from .lambda_labs_spider import LambdaLabsSpider

__all__ = [
    "BaseSpider",
    "APISpider",
    "OpenAISpider",
    "AnthropicSpider",
    "LambdaLabsSpider",
]

# 爬虫注册表
SPIDER_REGISTRY = {
    "openai": OpenAISpider,
    "anthropic": AnthropicSpider,
    "lambda_labs": LambdaLabsSpider,
}


def get_spider(name: str) -> type:
    """获取爬虫类"""
    return SPIDER_REGISTRY.get(name)


def list_spiders() -> list:
    """列出所有可用爬虫"""
    return list(SPIDER_REGISTRY.keys())
