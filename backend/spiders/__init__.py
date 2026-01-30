"""
爬虫包
"""

from .base import BaseSpider, APISpider
from .openai_spider import OpenAISpider
from .anthropic_spider import AnthropicSpider
from .lambda_labs_spider import LambdaLabsSpider
# 新增：中国大模型厂商
from .deepseek_spider import DeepSeekSpider
from .qwen_spider import QwenSpider
from .minimax_spider import MiniMaxSpider
# 新增：云厂商 GPU
from .aws_spider import AWSSpider
from .azure_spider import AzureSpider
from .gcp_spider import GCPSpider
# 新增：E板块 供应链
from .trendforce_spider import TrendForceSpider

__all__ = [
    "BaseSpider",
    "APISpider",
    "OpenAISpider",
    "AnthropicSpider",
    "LambdaLabsSpider",
    "DeepSeekSpider",
    "QwenSpider",
    "MiniMaxSpider",
    "AWSSpider",
    "AzureSpider",
    "GCPSpider",
    "TrendForceSpider",
]

# 爬虫注册表
SPIDER_REGISTRY = {
    # B板块：大模型 API
    "openai": OpenAISpider,
    "anthropic": AnthropicSpider,
    "deepseek": DeepSeekSpider,
    "qwen": QwenSpider,
    "minimax": MiniMaxSpider,
    # C板块：GPU 租赁
    "lambda_labs": LambdaLabsSpider,
    "aws": AWSSpider,
    "azure": AzureSpider,
    "gcp": GCPSpider,
    # E板块：供应链
    "trendforce": TrendForceSpider,
}


def get_spider(name: str) -> type:
    """获取爬虫类"""
    return SPIDER_REGISTRY.get(name)


def list_spiders() -> list:
    """列出所有可用爬虫"""
    return list(SPIDER_REGISTRY.keys())

