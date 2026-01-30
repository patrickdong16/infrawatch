"""
采集数据 API
提供 GPU 价格、推理覆盖率和 CapEx 数据的实时数据服务
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collected", tags=["Collected Data"])

# 数据目录
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


class CollectedDataResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    source: str = "collected"


def load_latest_json(subdir: str, prefix: str) -> Optional[Dict]:
    """加载目录下最新的 JSON 文件"""
    data_path = DATA_DIR / subdir
    if not data_path.exists():
        return None
    
    # 找到最新的文件
    json_files = sorted(data_path.glob(f"{prefix}*.json"), reverse=True)
    if not json_files:
        return None
    
    latest = json_files[0]
    try:
        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载 {latest} 失败: {e}")
        return None


@router.get("/gpu-prices", response_model=CollectedDataResponse)
async def get_gpu_prices():
    """
    获取最新 GPU 价格数据
    
    返回各云厂商的 GPU 实例价格，包括:
    - Lambda Labs
    - AWS
    - Azure
    - GCP
    """
    data = load_latest_json("gpu_prices", "prices_")
    if not data:
        raise HTTPException(status_code=404, detail="GPU 价格数据未找到")
    
    # 从 providers 数据中提取各 GPU 最低价
    key_gpus = {}
    gpu_types = ["H100", "H200", "A100", "B100", "B200"]
    
    for gpu_type in gpu_types:
        lowest_price = float('inf')
        best_provider = ""
        
        for provider, prices in data.get("providers", {}).items():
            for price_item in prices:
                specs = price_item.get("specs", {})
                item_gpu = specs.get("gpu_type", "").upper()
                if gpu_type.upper() in item_gpu:
                    price = price_item.get("price", 0)
                    if price > 0 and price < lowest_price:
                        lowest_price = price
                        best_provider = provider
        
        if lowest_price < float('inf'):
            key_gpus[gpu_type] = {
                "gpu_type": gpu_type,
                "lowest_price": lowest_price,
                "provider": best_provider,
            }
    
    return CollectedDataResponse(
        success=True,
        data={
            "providers": list(data.get("providers", {}).keys()),
            "key_gpus": key_gpus,
            "total_prices": sum(
                len(prices) for prices in data.get("providers", {}).values()
            ),
        },
        timestamp=data.get("timestamp"),
        source="gpu_price_collector",
    )



@router.get("/gpu-prices/detail", response_model=CollectedDataResponse)
async def get_gpu_prices_detail():
    """获取完整 GPU 价格详情"""
    data = load_latest_json("gpu_prices", "prices_")
    if not data:
        raise HTTPException(status_code=404, detail="GPU 价格数据未找到")
    
    return CollectedDataResponse(
        success=True,
        data=data,
        timestamp=data.get("timestamp"),
        source="gpu_price_collector",
    )


@router.get("/inference-coverage", response_model=CollectedDataResponse)
async def get_inference_coverage():
    """
    获取推理覆盖率相关数据
    
    返回:
    - RSS 相关文章
    - SEC 8-K 文件列表
    """
    data = load_latest_json("inference_coverage", "coverage_")
    if not data:
        raise HTTPException(status_code=404, detail="推理覆盖率数据未找到")
    
    # 按公司分组文章
    articles_by_company: Dict[str, List] = {}
    for article in data.get("relevant_articles", []):
        company = article.get("matched_company", "other")
        if company not in articles_by_company:
            articles_by_company[company] = []
        articles_by_company[company].append({
            "title": article.get("title"),
            "url": article.get("url"),
            "source": article.get("source"),
        })
    
    return CollectedDataResponse(
        success=True,
        data={
            "total_articles": data.get("rss_articles", 0),
            "relevant_count": len(data.get("relevant_articles", [])),
            "articles_by_company": articles_by_company,
            "sec_filings": data.get("sec_filings", {}),
        },
        timestamp=data.get("timestamp"),
        source="inference_coverage_collector",
    )


@router.get("/capex", response_model=CollectedDataResponse)
async def get_capex_data():
    """
    获取云厂商资本密集度数据
    
    返回:
    - Microsoft, Alphabet, Amazon, Meta 的 CapEx/Revenue 比率
    """
    data = load_latest_json("capex", "capex_")
    if not data:
        raise HTTPException(status_code=404, detail="CapEx 数据未找到")
    
    # 获取每家公司最新4季度数据
    companies_summary = {}
    for company, quarters in data.get("companies", {}).items():
        if quarters:
            # 按季度排序取最新4个
            sorted_quarters = sorted(
                quarters, 
                key=lambda x: x.get("period", ""), 
                reverse=True
            )[:4]
            
            avg_intensity = sum(
                q.get("capital_intensity_pct", 0) for q in sorted_quarters
            ) / len(sorted_quarters)
            
            companies_summary[company] = {
                "latest_period": sorted_quarters[0].get("period"),
                "latest_capex_b": sorted_quarters[0].get("capex_b"),
                "latest_revenue_b": sorted_quarters[0].get("total_revenue_b"),
                "avg_capital_intensity_4q": round(avg_intensity, 1),
                "history": sorted_quarters,
            }
    
    return CollectedDataResponse(
        success=True,
        data={
            "companies": companies_summary,
            "summary": data.get("summary", {}),
        },
        timestamp=data.get("timestamp"),
        source="capex_collector",
    )


@router.get("/news-feed", response_model=CollectedDataResponse)
async def get_news_feed():
    """
    获取 AI 领域最新新闻
    
    从采集的 RSS 数据中提取 AI 公司相关新闻
    """
    data = load_latest_json("inference_coverage", "coverage_")
    if not data:
        raise HTTPException(status_code=404, detail="新闻数据未找到")
    
    articles = data.get("relevant_articles", [])
    
    # 格式化为新闻列表
    news_items = []
    for article in articles:
        news_items.append({
            "title": article.get("title"),
            "url": article.get("url"),
            "company": article.get("matched_company", "").upper(),
            "source": _extract_source_name(article.get("source", "")),
            "collected_at": data.get("timestamp"),
        })
    
    return CollectedDataResponse(
        success=True,
        data={
            "news": news_items,
            "count": len(news_items),
        },
        timestamp=data.get("timestamp"),
        source="inference_coverage_collector",
    )


def _extract_source_name(url: str) -> str:
    """从 URL 提取来源名称"""
    if "techcrunch" in url:
        return "TechCrunch"
    if "theverge" in url:
        return "The Verge"
    if "arstechnica" in url:
        return "Ars Technica"
    return url.split("/")[2] if "/" in url else url
