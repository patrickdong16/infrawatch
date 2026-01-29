"""
MVP 数据 API
提供爬虫数据和派生指标的 REST 接口
"""

from fastapi import APIRouter
from typing import List, Dict, Any
import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/data", tags=["data"])


# 缓存数据
_cache = {
    "prices": None,
    "metrics": None,
}


async def get_spider_data():
    """获取所有爬虫数据"""
    from spiders import OpenAISpider, AnthropicSpider, LambdaLabsSpider
    
    all_data = []
    
    spiders = [
        ("openai", OpenAISpider()),
        ("anthropic", AnthropicSpider()),
        ("lambda_labs", LambdaLabsSpider()),
    ]
    
    for provider, spider in spiders:
        try:
            results = await spider.run()
            for item in results:
                item["provider"] = provider
            all_data.extend(results)
        except Exception as e:
            print(f"Error from {provider}: {e}")
    
    return all_data


async def get_derived_metrics():
    """获取派生指标"""
    from app.services.metrics_calculator import calculate_derived_metrics
    return await calculate_derived_metrics()


@router.get("/prices")
async def list_prices():
    """
    获取所有价格数据
    
    返回 OpenAI, Anthropic, Lambda Labs 的价格
    """
    global _cache
    
    if _cache["prices"] is None:
        _cache["prices"] = await get_spider_data()
    
    # 添加模拟趋势数据
    import random
    prices_with_trends = []
    for item in _cache["prices"]:
        item_copy = item.copy()
        item_copy["weekOverWeek"] = round(random.uniform(-10, 5), 1)
        item_copy["monthOverMonth"] = round(random.uniform(-15, 8), 1)
        item_copy["yearOverYear"] = round(random.uniform(-50, -20), 1)  # 年同比
        prices_with_trends.append(item_copy)
    
    return {
        "success": True,
        "data": prices_with_trends,
        "total": len(prices_with_trends),
    }



@router.get("/prices/{provider}")
async def get_provider_prices(provider: str):
    """获取特定提供商的价格"""
    global _cache
    
    if _cache["prices"] is None:
        _cache["prices"] = await get_spider_data()
    
    items = [p for p in _cache["prices"] if p.get("provider") == provider]
    
    return {
        "success": True,
        "data": items,
        "count": len(items),
    }


@router.get("/metrics")
async def list_metrics():
    """
    获取派生指标
    """
    global _cache
    
    if _cache["metrics"] is None:
        _cache["metrics"] = await get_derived_metrics()
    
    return {
        "success": True,
        "data": _cache["metrics"],
    }


@router.get("/summary")
async def get_summary():
    """
    获取仪表盘摘要数据
    """
    global _cache
    
    if _cache["prices"] is None:
        _cache["prices"] = await get_spider_data()
    if _cache["metrics"] is None:
        _cache["metrics"] = await get_derived_metrics()
    
    # 计算摘要
    prices = _cache["prices"]
    metrics = _cache["metrics"]
    
    # OpenAI GPT-4o 价格
    gpt4o_input = next((p for p in prices if p.get("sku_id") == "gpt-4o" and p.get("price_type") == "input"), None)
    
    # H100 价格
    h100 = next((p for p in prices if "h100" in p.get("sku_id", "").lower()), None)
    
    # 推理价格指数
    inference_index = next((m for m in metrics if m.get("metric_id") == "inference_price_index"), None)
    
    return {
        "success": True,
        "data": {
            "stage": {
                "current": "S1",
                "confidence": "MEDIUM",
                "description": "过渡期 - M01覆盖率在0.24-0.36区间",
            },
            "key_metrics": [
                {
                    "id": "m01_coverage",
                    "name": "M01 覆盖率",
                    "value": "0.24 - 0.36",
                    "status": "warning",
                    "weekOverWeek": 8.0,
                    "monthOverMonth": 12.5,
                    "yearOverYear": 85.0,
                },
                {
                    "id": "inference_price",
                    "name": "推理价格指数",
                    "value": inference_index.get("value") if inference_index else 2.73,
                    "unit": "$/M tokens",
                    "status": "good",
                    "weekOverWeek": -5.2,
                    "monthOverMonth": -12.8,
                    "yearOverYear": -45.0,
                },
                {
                    "id": "gpu_hourly",
                    "name": "H100 小时价",
                    "value": h100.get("price") if h100 else 2.49,
                    "unit": "$/hr",
                    "status": "neutral",
                    "weekOverWeek": -2.1,
                    "monthOverMonth": -8.5,
                    "yearOverYear": -35.0,
                },
            ],
            "providers": {
                "openai": len([p for p in prices if p.get("provider") == "openai"]),
                "anthropic": len([p for p in prices if p.get("provider") == "anthropic"]),
                "lambda_labs": len([p for p in prices if p.get("provider") == "lambda_labs"]),
            },
            "last_updated": __import__("datetime").datetime.now().isoformat(),
        },
    }


@router.post("/refresh")
async def refresh_data():
    """刷新缓存数据"""
    global _cache
    _cache = {"prices": None, "metrics": None}
    
    # 重新获取
    _cache["prices"] = await get_spider_data()
    _cache["metrics"] = await get_derived_metrics()
    
    return {
        "success": True,
        "message": "数据已刷新",
        "prices_count": len(_cache["prices"]),
        "metrics_count": len(_cache["metrics"]),
    }
