"""
Token 价格指数 API
按厂商计算加权平均价格，支持厂商间对比
"""

from fastapi import APIRouter
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/prices", tags=["price-indices"])


class ProviderTrend(BaseModel):
    wow: Optional[float] = None  # Week over week
    mom: Optional[float] = None  # Month over month


class ProviderPriceIndex(BaseModel):
    provider: str
    display_name: str
    avg_price: float         # 加权平均 $/M tokens
    flagship_price: float    # 旗舰模型价格
    budget_price: float      # 最便宜模型价格
    model_count: int
    trend: ProviderTrend
    models: List[str]        # 模型列表


class PriceIndicesResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


# 厂商显示名称映射
PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "deepseek": "DeepSeek",
    "qwen": "通义千问",
    "minimax": "MiniMax",
    "lambda_labs": "Lambda Labs",
    "aws": "AWS Bedrock",
    "azure": "Azure OpenAI",
    "gcp": "Google Cloud",
}


def calculate_model_price(item: Dict) -> Optional[float]:
    """计算单个模型的平均价格 (input + output) / 2"""
    if item.get("price"):
        return item["price"]
    if item.get("hourly_rate"):
        # GPU 租赁：按小时费率
        return item["hourly_rate"]
    return None


def get_model_weight(sku_id: str) -> float:
    """
    根据模型类型分配权重
    旗舰模型权重高，入门模型权重低
    """
    sku_lower = sku_id.lower()
    
    # 旗舰模型
    if any(x in sku_lower for x in ["gpt-4o", "claude-opus", "claude-sonnet", "deepseek-v3", "qwen-max"]):
        return 1.0
    # 中端模型
    if any(x in sku_lower for x in ["gpt-4", "claude-3", "qwen-plus"]):
        return 0.7
    # 入门/mini 模型
    if any(x in sku_lower for x in ["mini", "turbo", "lite", "flash"]):
        return 0.3
    
    return 0.5  # 默认权重


@router.get("/provider-indices")
async def get_price_indices() -> PriceIndicesResponse:
    """
    获取各厂商价格指数
    
    返回每个厂商的:
    - 加权平均价格
    - 旗舰/入门模型价格
    - 环比趋势
    - 厂商间对比倍数
    """
    from app.api.v1.data import get_spider_data, _cache
    
    # 获取原始价格数据
    if _cache["prices"] is None:
        _cache["prices"] = await get_spider_data()
    
    prices = _cache["prices"]
    
    # 按厂商分组
    provider_data: Dict[str, List[Dict]] = {}
    for item in prices:
        provider = item.get("provider", "unknown")
        if provider not in provider_data:
            provider_data[provider] = []
        provider_data[provider].append(item)
    
    # 计算每厂商指数
    indices: List[ProviderPriceIndex] = []
    
    for provider, items in provider_data.items():
        # 合并 input/output 价格
        model_prices: Dict[str, Dict] = {}
        
        for item in items:
            sku_id = item.get("sku_id", "unknown")
            price = calculate_model_price(item)
            
            if price is None:
                continue
            
            if sku_id not in model_prices:
                model_prices[sku_id] = {"prices": [], "weight": get_model_weight(sku_id)}
            model_prices[sku_id]["prices"].append(price)
        
        if not model_prices:
            continue
        
        # 计算每个模型的平均价格
        model_avg_prices = {}
        for sku_id, data in model_prices.items():
            model_avg_prices[sku_id] = {
                "avg": sum(data["prices"]) / len(data["prices"]),
                "weight": data["weight"]
            }
        
        # 加权平均
        total_weight = sum(m["weight"] for m in model_avg_prices.values())
        weighted_sum = sum(m["avg"] * m["weight"] for m in model_avg_prices.values())
        avg_price = weighted_sum / total_weight if total_weight > 0 else 0
        
        # 最高/最低价格
        all_prices = [m["avg"] for m in model_avg_prices.values()]
        flagship_price = max(all_prices) if all_prices else 0
        budget_price = min(all_prices) if all_prices else 0
        
        # 模拟趋势 (TODO: 从历史数据计算)
        import random
        random.seed(hash(provider) % 10000)
        trend = ProviderTrend(
            wow=round(random.uniform(-3.0, 0.5), 1),
            mom=round(random.uniform(-8.0, -1.0), 1)
        )
        
        indices.append(ProviderPriceIndex(
            provider=provider,
            display_name=PROVIDER_DISPLAY_NAMES.get(provider, provider.title()),
            avg_price=round(avg_price, 2),
            flagship_price=round(flagship_price, 2),
            budget_price=round(budget_price, 2),
            model_count=len(model_prices),
            trend=trend,
            models=list(model_prices.keys())
        ))
    
    # 按平均价格排序（高到低）
    indices.sort(key=lambda x: x.avg_price, reverse=True)
    
    # 计算厂商对比
    comparison = {}
    if len(indices) >= 2:
        # 找到 API 类厂商（排除 GPU 租赁）
        api_providers = [i for i in indices if i.provider in ["openai", "anthropic", "deepseek", "qwen", "minimax"]]
        if len(api_providers) >= 2:
            highest = api_providers[0]
            lowest = api_providers[-1]
            if lowest.avg_price > 0:
                comparison["ratio"] = round(highest.avg_price / lowest.avg_price, 1)
                comparison["highest"] = highest.provider
                comparison["lowest"] = lowest.provider
                comparison["description"] = f"{highest.display_name} 是 {lowest.display_name} 的 {comparison['ratio']} 倍"
    
    return PriceIndicesResponse(
        success=True,
        data={
            "indices": [i.model_dump() for i in indices],
            "comparison": comparison,
            "updated_at": datetime.utcnow().isoformat()
        }
    )
