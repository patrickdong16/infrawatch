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


def load_inference_coverage_config() -> Dict[str, Any]:
    """加载推理资产覆盖率 YAML 配置"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/inference_coverage.yml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading inference coverage config: {e}")
        return {}


def load_gpu_efficiency_config() -> Dict[str, Any]:
    """加载 GPU 效率 YAML 配置"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/gpu_efficiency.yml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading GPU efficiency config: {e}")
        return {}


@router.get("/ai-roi")
async def get_ai_roi() -> FinancialsResponse:
    """
    统一的 AI 投资回报 API
    
    整合两个视角:
    1. 推理资产覆盖率 (大模型公司): 推理收入 / 资产折旧
    2. 资本密集度 (云厂商): CapEx / 总收入
    
    核心问题: 投资产生的收入是否能逐步覆盖投入的成本？
    """
    # 加载推理覆盖率配置
    inference_config = load_inference_coverage_config()
    
    # 加载 Cloud 收入配置 (用于资本密集度计算)
    cloud_config = load_cloud_revenue_config()
    
    # === 1. 推理资产覆盖率 (大模型公司) ===
    inference_companies = []
    industry_avg = inference_config.get("industry_average", {})
    
    for company_key, company_data in inference_config.get("companies", {}).items():
        history = company_data.get("history", {})
        quarters = sorted(history.keys(), reverse=True)
        
        if quarters:
            latest = quarters[0]
            latest_data = history[latest]
            
            # 计算趋势
            trend = "stable"
            if len(quarters) >= 2:
                prev_data = history[quarters[1]]
                if latest_data["coverage_ratio"] > prev_data["coverage_ratio"]:
                    trend = "improving"
                elif latest_data["coverage_ratio"] < prev_data["coverage_ratio"]:
                    trend = "declining"
            
            inference_companies.append({
                "company": company_data["name"],
                "category": company_data["category"],
                "latest_quarter": latest,
                "coverage_ratio": latest_data["coverage_ratio"],
                "inference_revenue_b": latest_data["inference_revenue_b"],
                "asset_depreciation_b": latest_data["asset_depreciation_b"],
                "trend": trend,
            })
    
    # 行业平均趋势
    avg_quarters = sorted(industry_avg.keys(), reverse=True)
    current_avg = industry_avg.get(avg_quarters[0], 0) if avg_quarters else 0
    prev_avg = industry_avg.get(avg_quarters[1], 0) if len(avg_quarters) >= 2 else 0
    
    # === 2. 资本密集度 (云厂商) ===
    # 从 EODHD 获取最新数据
    capital_intensity_data = []
    total_revenue = 0
    total_capex = 0
    
    cloud_companies = ["MSFT.US", "GOOGL.US", "AMZN.US"]
    for ticker in cloud_companies:
        fundamentals = await fetch_fundamentals(ticker)
        if fundamentals:
            history = extract_quarterly_data(fundamentals)
            if history:
                latest = history[0]
                revenue = latest.revenue or 0
                capex = abs(latest.capex or 0)
                
                total_revenue += revenue
                total_capex += capex
                
                intensity = round(capex / revenue * 100, 1) if revenue > 0 else 0
                
                capital_intensity_data.append({
                    "ticker": ticker,
                    "name": ticker.split(".")[0],
                    "quarter": latest.quarter,
                    "revenue_b": round(revenue / 1e9, 1),
                    "capex_b": round(capex / 1e9, 1),
                    "capital_intensity": intensity,
                })
    
    overall_intensity = round(total_capex / total_revenue * 100, 1) if total_revenue > 0 else 0
    
    # === 3. 趋势分析 ===
    # 覆盖率历史趋势
    coverage_trend = []
    for q in sorted(industry_avg.keys()):
        coverage_trend.append({
            "quarter": q,
            "coverage_ratio": industry_avg[q],
            "threshold": 1.0,  # 盈亏平衡线
        })
    
    # 判断整体趋势
    if current_avg >= 1.0 and current_avg > prev_avg:
        overall_trend = "sustainable"
        trend_description = "覆盖率超过盈亏平衡线且持续改善"
    elif current_avg >= 1.0:
        overall_trend = "balanced"
        trend_description = "覆盖率达到盈亏平衡"
    elif current_avg > prev_avg:
        overall_trend = "improving"
        trend_description = "覆盖率持续提升，有望达到盈亏平衡"
    else:
        overall_trend = "challenging"
        trend_description = "覆盖率下降，需关注投资回报"
    
    return FinancialsResponse(
        success=True,
        data={
            "core_question": "投资产生的收入是否能逐步覆盖投入的成本？",
            "overall_verdict": {
                "trend": overall_trend,
                "description": trend_description,
                "current_coverage": current_avg,
                "previous_coverage": prev_avg,
                "change": round(current_avg - prev_avg, 2),
            },
            "inference_coverage": {
                "title": "推理资产覆盖率",
                "description": "AI推理收入 / 资产年化折旧",
                "perspective": "大模型公司",
                "industry_average": current_avg,
                "companies": inference_companies,
                "trend_series": coverage_trend,
            },
            "capital_intensity": {
                "title": "资本密集度",
                "description": "CapEx / 总收入",
                "perspective": "云厂商",
                "overall": overall_intensity,
                "companies": capital_intensity_data,
            },
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


@router.get("/gpu-efficiency")
async def get_gpu_efficiency() -> FinancialsResponse:
    """
    GPU 算力成本效率指数
    
    性能归一化法: 追踪每 PFLOPS 成本的变化
    基准期: 2024-Q1 = 100
    """
    config = load_gpu_efficiency_config()
    
    gpu_specs = config.get("gpu_specs", {})
    price_history = config.get("price_history", {})
    benchmark = config.get("benchmark_task", {})
    base_period = config.get("base_period", "2024-Q1")
    
    # 计算每个季度的效率指数
    index_series = []
    base_cost_per_pflops = None
    
    for quarter in sorted(price_history.keys()):
        prices = price_history[quarter]
        
        # 计算该季度每个 GPU 的 $/PFLOPS
        cost_per_pflops_list = []
        for gpu_key, price in prices.items():
            spec = gpu_specs.get(gpu_key)
            if spec and spec.get("fp16_tflops"):
                pflops = spec["fp16_tflops"] / 1000  # TFLOPS to PFLOPS
                cost_per_pflops = price / pflops
                cost_per_pflops_list.append(cost_per_pflops)
        
        if cost_per_pflops_list:
            # 使用最低成本 (代表最优选择)
            best_cost = min(cost_per_pflops_list)
            avg_cost = sum(cost_per_pflops_list) / len(cost_per_pflops_list)
            
            if quarter == base_period:
                base_cost_per_pflops = best_cost
            
            index_value = round(base_cost_per_pflops / best_cost * 100, 1) if base_cost_per_pflops else 100
            
            index_series.append({
                "quarter": quarter,
                "index": index_value,
                "best_cost_per_pflops": round(best_cost, 3),
                "avg_cost_per_pflops": round(avg_cost, 3),
            })
    
    # 计算任务成本指数 (标准推理任务)
    task_cost_series = []
    base_task_cost = None
    throughput = benchmark.get("throughput", {})
    
    for quarter in sorted(price_history.keys()):
        prices = price_history[quarter]
        
        # 每个 GPU 完成任务的成本
        task_costs = []
        for gpu_key, price in prices.items():
            tput = throughput.get(gpu_key, 0)
            if tput > 0:
                # 完成 100万 token 需要的时间和成本
                tokens = benchmark.get("tokens", 1000000)
                hours_needed = tokens / tput / 3600
                cost = price * hours_needed
                task_costs.append({"gpu": gpu_key, "cost": cost})
        
        if task_costs:
            best = min(task_costs, key=lambda x: x["cost"])
            
            if quarter == base_period:
                base_task_cost = best["cost"]
            
            index_value = round(base_task_cost / best["cost"] * 100, 1) if base_task_cost else 100
            
            task_cost_series.append({
                "quarter": quarter,
                "index": index_value,
                "best_gpu": best["gpu"],
                "cost_usd": round(best["cost"], 2),
            })
    
    # 最新指数
    latest = index_series[-1] if index_series else {"index": 100}
    latest_task = task_cost_series[-1] if task_cost_series else {"index": 100}
    
    return FinancialsResponse(
        success=True,
        data={
            "title": "算力成本效率指数",
            "description": "性能归一化法 - 追踪每 PFLOPS 成本变化",
            "base_period": base_period,
            "base_index": 100,
            "current": {
                "pflops_index": latest.get("index", 100),
                "task_index": latest_task.get("index", 100),
                "interpretation": "指数 > 100 表示效率提升（成本下降）",
            },
            "pflops_series": index_series,
            "task_series": task_cost_series,
            "gpu_specs": {k: {"name": v["name"], "fp16_tflops": v["fp16_tflops"]} 
                         for k, v in gpu_specs.items()},
            "updated_at": datetime.utcnow().isoformat(),
        }
    )
