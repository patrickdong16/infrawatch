"""
CapEx 资本密集度数据采集器
从 SEC 财报和公开数据源获取云厂商资本支出数据
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import httpx

logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = Path(__file__).parent.parent / "data" / "capex"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CapExDataPoint:
    """CapEx 数据点"""
    company: str
    period: str  # e.g., "2025-Q4"
    total_revenue_b: float
    capex_b: float
    capital_intensity_pct: float
    ai_capex_estimate_b: Optional[float] = None
    source: str = ""
    source_url: str = ""
    updated_at: str = ""


class CapExCollector:
    """
    资本密集度数据采集器
    
    目标公司 (上市):
    - Microsoft (MSFT)
    - Alphabet/Google (GOOGL)
    - Amazon (AMZN)
    - Meta (META)
    
    数据来源:
    1. SEC 10-Q/10-K 文件
    2. 公司财报页面
    3. Financial Modeling Prep API (免费tier)
    """
    
    # 目标公司 SEC CIK
    COMPANIES = {
        "Microsoft": {
            "ticker": "MSFT",
            "cik": "0000789019",
            "ir_url": "https://www.microsoft.com/investor",
        },
        "Alphabet": {
            "ticker": "GOOGL",
            "cik": "0001652044",
            "ir_url": "https://abc.xyz/investor/",
        },
        "Amazon": {
            "ticker": "AMZN",
            "cik": "0001018724",
            "ir_url": "https://ir.aboutamazon.com/",
        },
        "Meta": {
            "ticker": "META",
            "cik": "0001326801",
            "ir_url": "https://investor.fb.com/",
        },
    }
    
    # SEC Edgar API
    SEC_EDGAR_BASE = "https://data.sec.gov"
    
    def __init__(self, timeout: int = 15, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.headers = {
            "User-Agent": "InfraWatch/1.0 (research@example.com)",
            "Accept": "application/json",
        }
    
    async def _fetch_json(self, url: str) -> Optional[Dict]:
        """HTTP GET JSON with retry"""
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, headers=self.headers)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                logger.warning(f"Fetch failed ({attempt+1}/{self.retries}): {url} - {e}")
                await asyncio.sleep(1 * (attempt + 1))
        return None
    
    async def fetch_company_facts(self, cik: str) -> Optional[Dict]:
        """从SEC获取公司XBRL财务数据"""
        url = f"{self.SEC_EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        return await self._fetch_json(url)
    
    def extract_capex_from_facts(self, facts: Dict, company: str) -> List[CapExDataPoint]:
        """从 XBRL facts 提取 CapEx 数据"""
        data_points = []
        
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        
        # 常见 CapEx 字段
        capex_keys = [
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "CapitalExpendituresIncurredButNotYetPaid",
        ]
        
        revenue_keys = [
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
        ]
        
        # 查找 CapEx
        capex_data = {}
        for key in capex_keys:
            if key in us_gaap:
                units = us_gaap[key].get("units", {})
                usd = units.get("USD", [])
                for entry in usd:
                    if entry.get("form") in ["10-Q", "10-K"]:
                        period = str(entry.get("fy", "")) + "-" + str(entry.get("fp", ""))
                        value = entry.get("val", 0) / 1e9  # 转为 billion
                        capex_data[period] = value
                break
        
        # 查找 Revenue
        revenue_data = {}
        for key in revenue_keys:
            if key in us_gaap:
                units = us_gaap[key].get("units", {})
                usd = units.get("USD", [])
                for entry in usd:
                    if entry.get("form") in ["10-Q", "10-K"]:
                        period = str(entry.get("fy", "")) + "-" + str(entry.get("fp", ""))
                        value = entry.get("val", 0) / 1e9
                        revenue_data[period] = value
                break
        
        # 组合数据
        for period in capex_data:
            if period in revenue_data and revenue_data[period] > 0:
                capex = capex_data[period]
                revenue = revenue_data[period]
                intensity = (capex / revenue) * 100
                
                data_points.append(CapExDataPoint(
                    company=company,
                    period=period,
                    total_revenue_b=round(revenue, 2),
                    capex_b=round(capex, 2),
                    capital_intensity_pct=round(intensity, 1),
                    source="SEC XBRL",
                    source_url=f"{self.SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={self.COMPANIES.get(company, {}).get('cik', '')}",
                    updated_at=datetime.now().isoformat(),
                ))
        
        return data_points
    
    async def collect_company(self, company: str, info: Dict) -> List[CapExDataPoint]:
        """采集单个公司的 CapEx 数据"""
        cik = info.get("cik", "")
        if not cik:
            return []
        
        logger.info(f"[{company}] 正在采集 SEC 数据...")
        
        facts = await self.fetch_company_facts(cik)
        if not facts:
            logger.warning(f"[{company}] 无法获取 SEC 数据")
            return []
        
        data_points = self.extract_capex_from_facts(facts, company)
        logger.info(f"[{company}] 提取到 {len(data_points)} 个季度数据")
        
        return data_points
    
    async def collect_all(self) -> Dict[str, Any]:
        """采集所有公司"""
        logger.info("开始 CapEx 资本密集度采集...")
        
        all_data = {}
        
        for company, info in self.COMPANIES.items():
            data_points = await self.collect_company(company, info)
            all_data[company] = [asdict(dp) for dp in data_points]
            # 避免请求过快
            await asyncio.sleep(0.5)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "companies": all_data,
            "summary": self._generate_summary(all_data),
        }
        
        # 保存结果
        self.save_result(result)
        
        return result
    
    def _generate_summary(self, all_data: Dict) -> Dict:
        """生成摘要"""
        summary = {}
        
        for company, data_points in all_data.items():
            if data_points:
                # 取最近4个季度
                recent = sorted(data_points, key=lambda x: x.get("period", ""), reverse=True)[:4]
                avg_intensity = sum(d.get("capital_intensity_pct", 0) for d in recent) / len(recent)
                summary[company] = {
                    "latest_period": recent[0].get("period") if recent else "",
                    "avg_capital_intensity_4q": round(avg_intensity, 1),
                    "total_quarters": len(data_points),
                }
        
        return summary
    
    def save_result(self, result: Dict) -> str:
        """保存采集结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = DATA_DIR / f"capex_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"采集结果已保存: {filename}")
        return str(filename)


async def main():
    """CLI入口"""
    logging.basicConfig(level=logging.INFO)
    collector = CapExCollector()
    result = await collector.collect_all()
    
    print("\n=== CapEx 采集汇总 ===")
    for company, summary in result.get("summary", {}).items():
        print(f"{company}:")
        print(f"  最新: {summary.get('latest_period')}")
        print(f"  4Q平均资本密集度: {summary.get('avg_capital_intensity_4q')}%")


if __name__ == "__main__":
    asyncio.run(main())
