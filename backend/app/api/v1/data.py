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
    from spiders import (
        OpenAISpider, AnthropicSpider, LambdaLabsSpider,
        DeepSeekSpider, QwenSpider, MiniMaxSpider,
        AWSSpider, AzureSpider, GCPSpider
    )
    
    all_data = []
    
    spiders = [
        # B板块：大模型 API
        ("openai", OpenAISpider()),
        ("anthropic", AnthropicSpider()),
        ("deepseek", DeepSeekSpider()),
        ("qwen", QwenSpider()),
        ("minimax", MiniMaxSpider()),
        # C板块：GPU 租赁
        ("lambda_labs", LambdaLabsSpider()),
        ("aws", AWSSpider()),
        ("azure", AzureSpider()),
        ("gcp", GCPSpider()),
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
    
    # 使用数据库计算真实趋势数据
    from app.repositories.price_history import save_and_enrich_prices
    prices_with_trends = save_and_enrich_prices(_cache["prices"])
    
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
            ],
            "providers": {
                "openai": len([p for p in prices if p.get("provider") == "openai"]),
                "anthropic": len([p for p in prices if p.get("provider") == "anthropic"]),
                "deepseek": len([p for p in prices if p.get("provider") == "deepseek"]),
                "qwen": len([p for p in prices if p.get("provider") == "qwen"]),
                "minimax": len([p for p in prices if p.get("provider") == "minimax"]),
                "lambda_labs": len([p for p in prices if p.get("provider") == "lambda_labs"]),
                "aws": len([p for p in prices if p.get("provider") == "aws"]),
                "azure": len([p for p in prices if p.get("provider") == "azure"]),
                "gcp": len([p for p in prices if p.get("provider") == "gcp"]),
            },
            "last_updated": __import__("datetime").datetime.now().isoformat(),
        },
    }


@router.get("/stage/current")
async def get_current_stage():
    """
    获取当前阶段判定
    
    基于 StageEngine 计算当前 S0-S3 阶段
    """
    from app.domain.stage_engine import StageEngine, StageMetrics
    
    engine = StageEngine()
    
    # 使用实际数据或模拟数据计算阶段
    # 在 MVP 阶段使用默认指标
    metrics = StageMetrics(
        m01_low=0.24,
        m01_high=0.36,
        b_qoq_deflation=0.12,  # 12% 季度通缩
        c_spot_discount=0.15,  # 15% spot 折扣
        c_rental_qoq=-0.08,
        a_growth_streak=2,
        d3_margin_qoq=0.02,
        e_supply_tightness=0.6,
    )
    
    result = engine.determine(metrics)
    
    return {
        "success": True,
        "data": {
            "stage": result.stage.value,
            "confidence": result.confidence.value,
            "rationale": result.rationale,
            "trigger_conditions": result.trigger_conditions,
            "transition_risks": result.transition_risks,
            "metrics_snapshot": result.metrics_snapshot,
            "determined_at": result.determined_at.isoformat(),
        },
    }


@router.get("/signals")
async def list_signals():
    """
    获取最近的信号列表
    """
    from app.domain.signal_detector import get_detector
    
    detector = get_detector()
    signals = detector.get_recent_signals(limit=20)
    
    return {
        "success": True,
        "data": [detector.to_dict(s) for s in signals],
        "total": len(signals),
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
