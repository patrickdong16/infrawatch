"""
财务指标 API (EODHD 数据源)
获取 AI 相关公司的财报数据，计算收入/投入增速对比
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import httpx
import os

router = APIRouter(prefix="/financials", tags=["financials"])

# EODHD API 配置
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "6963a7c9539338.94496324")
EODHD_BASE_URL = "https://eodhd.com/api"

# 监控的 AI 相关公司
AI_COMPANIES = [
    {"ticker": "MSFT.US", "name": "Microsoft", "focus": "Azure AI"},
    {"ticker": "GOOGL.US", "name": "Alphabet", "focus": "Google Cloud AI"},
    {"ticker": "AMZN.US", "name": "Amazon", "focus": "AWS AI"},
    {"ticker": "META.US", "name": "Meta", "focus": "AI Infrastructure"},
    {"ticker": "NVDA.US", "name": "Nvidia", "focus": "AI GPU"},
    {"ticker": "TSLA.US", "name": "Tesla", "focus": "AI/FSD"},
]


class QuarterlyData(BaseModel):
    quarter: str
    revenue: Optional[float] = None
    capex: Optional[float] = None
    rd_expense: Optional[float] = None


class CompanyFinancials(BaseModel):
    ticker: str
    name: str
    focus: str
    latest_quarter: str
    revenue: float
    revenue_qoq: Optional[float] = None
    capex: float
    capex_qoq: Optional[float] = None
    history: List[QuarterlyData]


class FinancialsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


async def fetch_fundamentals(ticker: str) -> Optional[Dict]:
    """从 EODHD 获取公司财报数据"""
    url = f"{EODHD_BASE_URL}/fundamentals/{ticker}"
    params = {
        "api_token": EODHD_API_KEY,
        "fmt": "json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
    
    return None


def extract_quarterly_data(fundamentals: Dict) -> List[QuarterlyData]:
    """从财报数据中提取季度信息"""
    income = fundamentals.get("Financials", {}).get("Income_Statement", {}).get("quarterly", {})
    cash_flow = fundamentals.get("Financials", {}).get("Cash_Flow", {}).get("quarterly", {})
    
    # 获取最近 8 个季度
    quarters = sorted(income.keys(), reverse=True)[:8]
    
    result = []
    for q in quarters:
        inc_data = income.get(q, {})
        cf_data = cash_flow.get(q, {})
        
        result.append(QuarterlyData(
            quarter=q,
            revenue=inc_data.get("totalRevenue"),
            capex=cf_data.get("capitalExpenditures"),
            rd_expense=inc_data.get("researchDevelopment"),
        ))
    
    return result


def calculate_qoq(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """计算季度环比增速"""
    if current is None or previous is None or previous == 0:
        return None
    return round((current / previous - 1) * 100, 1)


@router.get("/ai-metrics")
async def get_ai_financials() -> FinancialsResponse:
    """
    获取 AI 相关公司的财务指标
    
    返回:
    - 各公司最新季度收入、CapEx
    - QoQ 增速对比
    - 8 季度历史数据
    """
    companies_data: List[CompanyFinancials] = []
    
    for company in AI_COMPANIES:
        ticker = company["ticker"]
        fundamentals = await fetch_fundamentals(ticker)
        
        if not fundamentals:
            continue
        
        history = extract_quarterly_data(fundamentals)
        
        if len(history) < 2:
            continue
        
        latest = history[0]
        previous = history[1]
        
        companies_data.append(CompanyFinancials(
            ticker=ticker,
            name=company["name"],
            focus=company["focus"],
            latest_quarter=latest.quarter,
            revenue=latest.revenue or 0,
            revenue_qoq=calculate_qoq(latest.revenue, previous.revenue),
            capex=latest.capex or 0,
            capex_qoq=calculate_qoq(latest.capex, previous.capex),
            history=history,
        ))
    
    # 计算汇总统计
    total_revenue = sum(c.revenue for c in companies_data)
    total_capex = sum(c.capex for c in companies_data)
    avg_revenue_growth = sum(c.revenue_qoq or 0 for c in companies_data) / len(companies_data) if companies_data else 0
    avg_capex_growth = sum(c.capex_qoq or 0 for c in companies_data) / len(companies_data) if companies_data else 0
    
    return FinancialsResponse(
        success=True,
        data={
            "companies": [c.model_dump() for c in companies_data],
            "summary": {
                "total_revenue_b": round(total_revenue / 1e9, 1),
                "total_capex_b": round(total_capex / 1e9, 1),
                "avg_revenue_qoq": round(avg_revenue_growth, 1),
                "avg_capex_qoq": round(avg_capex_growth, 1),
                "capex_to_revenue_ratio": round(total_capex / total_revenue * 100, 1) if total_revenue > 0 else 0,
            },
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


@router.get("/growth-comparison")
async def get_growth_comparison() -> FinancialsResponse:
    """
    获取 AI 收入增速 vs 投入增速 (CapEx) 对比数据
    用于绘制双曲线对比图
    """
    all_quarters: Dict[str, Dict[str, float]] = {}
    
    for company in AI_COMPANIES:
        ticker = company["ticker"]
        fundamentals = await fetch_fundamentals(ticker)
        
        if not fundamentals:
            continue
        
        history = extract_quarterly_data(fundamentals)
        
        for i, q in enumerate(history[:-1]):
            if q.quarter not in all_quarters:
                all_quarters[q.quarter] = {"revenue": 0, "capex": 0, "prev_revenue": 0, "prev_capex": 0}
            
            next_q = history[i + 1]
            all_quarters[q.quarter]["revenue"] += q.revenue or 0
            all_quarters[q.quarter]["capex"] += q.capex or 0
            all_quarters[q.quarter]["prev_revenue"] += next_q.revenue or 0
            all_quarters[q.quarter]["prev_capex"] += next_q.capex or 0
    
    # 转换为时间序列
    series = []
    for quarter in sorted(all_quarters.keys()):
        data = all_quarters[quarter]
        series.append({
            "quarter": quarter,
            "revenue_qoq": calculate_qoq(data["revenue"], data["prev_revenue"]),
            "capex_qoq": calculate_qoq(data["capex"], data["prev_capex"]),
        })
    
    return FinancialsResponse(
        success=True,
        data={
            "series": series,
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


def load_cloud_revenue_config() -> Dict[str, Any]:
    """加载 Cloud 收入 YAML 配置"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/cloud_revenue.yml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading cloud revenue config: {e}")
        return {}


@router.get("/sustainability")
async def get_sustainability_metrics() -> FinancialsResponse:
    """
    AI 可持续性评分卡数据
    
    返回:
    - capital_intensity: 资本密集度 (CapEx / 总收入)
    - cloud_revenue: Cloud 业务收入 (Azure, GCP, AWS)
    - growth_comparison: Cloud收入增速 vs CapEx增速
    """
    # 1. 获取 EODHD 财务数据用于 CapEx 和总收入
    cloud_companies = ["MSFT.US", "GOOGL.US", "AMZN.US"]
    total_revenue = 0
    total_capex = 0
    prev_revenue = 0
    prev_capex = 0
    
    for ticker in cloud_companies:
        fundamentals = await fetch_fundamentals(ticker)
        if fundamentals:
            history = extract_quarterly_data(fundamentals)
            if len(history) >= 2:
                total_revenue += history[0].revenue or 0
                total_capex += abs(history[0].capex or 0)
                prev_revenue += history[1].revenue or 0
                prev_capex += abs(history[1].capex or 0)
    
    # 2. 加载 Cloud 收入配置
    cloud_config = load_cloud_revenue_config()
    
    cloud_revenue_data = []
    total_cloud_revenue = 0
    prev_cloud_revenue = 0
    
    for company_key, company_data in cloud_config.items():
        history = company_data.get("history", [])
        if len(history) >= 2:
            latest = history[0]
            previous = history[1]
            revenue = latest.get("revenue", 0)
            prev_rev = previous.get("revenue", 0)
            
            total_cloud_revenue += revenue
            prev_cloud_revenue += prev_rev
            
            cloud_revenue_data.append({
                "company": company_key.title(),
                "segment": company_data.get("name", ""),
                "revenue_m": revenue,
                "revenue_b": round(revenue / 1000, 1),
                "yoy_growth": latest.get("yoy_growth"),
                "qoq_growth": round((revenue / prev_rev - 1) * 100, 1) if prev_rev > 0 else None,
                "quarter": latest.get("quarter", ""),
            })
    
    # 3. 计算指标
    capital_intensity = round(total_capex / total_revenue * 100, 1) if total_revenue > 0 else 0
    capital_intensity_qoq = round(
        (total_capex / total_revenue - prev_capex / prev_revenue) * 100, 1
    ) if prev_revenue > 0 and prev_capex > 0 else 0
    
    cloud_growth = round((total_cloud_revenue / prev_cloud_revenue - 1) * 100, 1) if prev_cloud_revenue > 0 else 0
    capex_growth = calculate_qoq(total_capex, prev_capex) or 0
    growth_spread = round(cloud_growth - capex_growth, 1)
    
    # 4. 生成增速对比时间序列 (从 Cloud 配置中提取)
    # 按季度聚合
    quarter_series = {}
    for company_key, company_data in cloud_config.items():
        for item in company_data.get("history", []):
            q = item.get("quarter", "")
            if q not in quarter_series:
                quarter_series[q] = {"cloud_revenue": 0}
            quarter_series[q]["cloud_revenue"] += item.get("revenue", 0)
    
    # 计算 Cloud 增速序列
    sorted_quarters = sorted(quarter_series.keys())
    growth_series = []
    for i, q in enumerate(sorted_quarters):
        if i == 0:
            continue
        prev_q = sorted_quarters[i - 1]
        current = quarter_series[q]["cloud_revenue"]
        previous = quarter_series[prev_q]["cloud_revenue"]
        growth_series.append({
            "quarter": q,
            "cloud_growth": round((current / previous - 1) * 100, 1) if previous > 0 else 0,
            "capex_growth": None,  # 需要从 EODHD 获取历史 CapEx
        })
    
    return FinancialsResponse(
        success=True,
        data={
            "capital_intensity": {
                "current": capital_intensity,
                "qoq_change": capital_intensity_qoq,
                "trend": "up" if capital_intensity_qoq > 0 else "down",
                "description": "资本密集度 = CapEx / 总收入",
            },
            "cloud_revenue": {
                "total_b": round(total_cloud_revenue / 1000, 1),
                "qoq_growth": cloud_growth,
                "companies": sorted(cloud_revenue_data, key=lambda x: x["revenue_m"], reverse=True),
            },
            "growth_comparison": {
                "cloud_growth": cloud_growth,
                "capex_growth": capex_growth,
                "spread": growth_spread,
                "spread_trend": "positive" if growth_spread > 0 else "negative",
                "series": growth_series,
            },
            "updated_at": datetime.utcnow().isoformat(),
        }
    )
