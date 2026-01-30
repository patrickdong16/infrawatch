"""
推理覆盖率数据采集器
从新闻/RSS/SEC 文件监测 AI 公司营收和资产数据
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import httpx

logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = Path(__file__).parent.parent / "data" / "inference_coverage"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CoverageDataPoint:
    """推理覆盖率数据点"""
    company: str
    period: str  # e.g., "2025-M12" or "2025-Q4"
    inference_revenue_b: Optional[float] = None
    asset_depreciation_b: Optional[float] = None
    coverage_ratio: Optional[float] = None
    source: str = ""
    source_url: str = ""
    confidence: str = "low"  # low, medium, high
    updated_at: str = ""


class InferenceCoverageCollector:
    """
    推理覆盖率数据采集器
    
    数据来源:
    1. RSS订阅 (The Information, Bloomberg, WSJ)
    2. SEC Edgar 8-K 文件
    3. 公司博客/新闻
    """
    
    # 目标公司
    TARGET_COMPANIES = {
        "openai": ["OpenAI", "Sam Altman", "ChatGPT revenue"],
        "anthropic": ["Anthropic", "Claude", "Dario Amodei"],
        "microsoft": ["Microsoft Azure AI", "Microsoft AI", "Microsoft Copilot revenue"],
        "google": ["Google Cloud AI", "Vertex AI", "Google AI revenue"],
        "amazon": ["AWS AI", "Amazon Bedrock", "AWS machine learning"],
    }
    
    # RSS源
    RSS_FEEDS = [
        # 公开RSS
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
    ]
    
    # SEC Edgar API
    SEC_EDGAR_BASE = "https://data.sec.gov"
    SEC_TICKERS = {
        "microsoft": "0000789019",
        "google": "0001652044",  # Alphabet
        "amazon": "0001018724",
    }
    
    def __init__(self, timeout: int = 10, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.headers = {
            "User-Agent": "InfraWatch/1.0 (research@infrawatch.io)",
            "Accept": "application/json, application/xml, text/xml",
        }
    
    async def _fetch(self, url: str) -> Optional[str]:
        """HTTP GET with retry"""
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, headers=self.headers)
                    resp.raise_for_status()
                    return resp.text
            except Exception as e:
                logger.warning(f"Fetch failed ({attempt+1}/{self.retries}): {url} - {e}")
                await asyncio.sleep(1 * (attempt + 1))
        return None
    
    async def fetch_rss_feed(self, feed_url: str) -> List[Dict]:
        """从RSS获取文章列表"""
        content = await self._fetch(feed_url)
        if not content:
            return []
        
        articles = []
        
        # 简单解析 RSS XML
        # 查找 <item> 或 <entry> 标签
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(content)
            # RSS 2.0
            items = root.findall(".//item")
            # Atom
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            
            for item in items[:20]:  # 只取最新20条
                title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or ""
                link = item.findtext("link") or ""
                if not link:
                    link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                    if link_elem is not None:
                        link = link_elem.get("href", "")
                
                articles.append({
                    "title": title,
                    "url": link,
                    "source": feed_url,
                })
        except Exception as e:
            logger.error(f"RSS解析失败: {e}")
        
        return articles
    
    def filter_relevant_articles(self, articles: List[Dict]) -> List[Dict]:
        """筛选与目标公司相关的文章"""
        relevant = []
        
        # 构建匹配关键词
        all_keywords = []
        for company, keywords in self.TARGET_COMPANIES.items():
            all_keywords.extend([(kw, company) for kw in keywords])
        
        for article in articles:
            title = article.get("title", "").lower()
            for keyword, company in all_keywords:
                if keyword.lower() in title:
                    article["matched_company"] = company
                    article["matched_keyword"] = keyword
                    relevant.append(article)
                    break
        
        return relevant
    
    async def fetch_sec_filings(self, cik: str, form_type: str = "8-K") -> List[Dict]:
        """从SEC Edgar获取公司文件"""
        url = f"{self.SEC_EDGAR_BASE}/submissions/CIK{cik}.json"
        
        content = await self._fetch(url)
        if not content:
            return []
        
        try:
            data = json.loads(content)
            filings = data.get("filings", {}).get("recent", {})
            
            forms = []
            form_types = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accessions = filings.get("accessionNumber", [])
            
            for i, ft in enumerate(form_types[:50]):
                if form_type in ft:
                    forms.append({
                        "form_type": ft,
                        "filing_date": dates[i] if i < len(dates) else "",
                        "accession": accessions[i] if i < len(accessions) else "",
                        "company": data.get("name", ""),
                    })
            
            return forms
        except Exception as e:
            logger.error(f"SEC解析失败: {e}")
            return []
    
    def extract_revenue_mentions(self, text: str, company: str) -> Optional[CoverageDataPoint]:
        """从文本中提取收入相关数据"""
        # 正则匹配金额
        # 例如: "$2 billion", "$2.5B", "2.5 billion dollars"
        amount_pattern = r"\$?([\d.]+)\s*(billion|B|million|M)"
        
        matches = re.findall(amount_pattern, text, re.I)
        if not matches:
            return None
        
        # 简单提取第一个提到的金额
        for amount, unit in matches:
            value = float(amount)
            if unit.lower() in ["million", "m"]:
                value /= 1000  # 转换为billion
            
            return CoverageDataPoint(
                company=company,
                period=datetime.now().strftime("%Y-M%m"),
                inference_revenue_b=value,
                source="news_extraction",
                confidence="low",
                updated_at=datetime.now().isoformat(),
            )
        
        return None
    
    async def collect_all(self) -> Dict[str, Any]:
        """执行全量采集"""
        logger.info("开始推理覆盖率数据采集...")
        
        all_articles = []
        
        # 1. 采集RSS
        for feed_url in self.RSS_FEEDS:
            articles = await self.fetch_rss_feed(feed_url)
            all_articles.extend(articles)
            logger.info(f"[RSS] {feed_url}: {len(articles)} 篇")
        
        # 2. 筛选相关文章
        relevant = self.filter_relevant_articles(all_articles)
        logger.info(f"[筛选] 相关文章: {len(relevant)}")
        
        # 3. 采集SEC文件
        sec_filings = {}
        for company, cik in self.SEC_TICKERS.items():
            filings = await self.fetch_sec_filings(cik)
            sec_filings[company] = filings
            logger.info(f"[SEC] {company}: {len(filings)} 份8-K")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "rss_articles": len(all_articles),
            "relevant_articles": relevant,
            "sec_filings": sec_filings,
        }
        
        # 保存结果
        self.save_result(result)
        
        return result
    
    def save_result(self, result: Dict) -> str:
        """保存采集结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = DATA_DIR / f"coverage_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"采集结果已保存: {filename}")
        return str(filename)


async def main():
    """CLI入口"""
    logging.basicConfig(level=logging.INFO)
    collector = InferenceCoverageCollector()
    result = await collector.collect_all()
    
    print("\n=== 采集结果汇总 ===")
    print(f"RSS文章: {result['rss_articles']}")
    print(f"相关文章: {len(result['relevant_articles'])}")
    for article in result['relevant_articles'][:5]:
        print(f"  - [{article.get('matched_company')}] {article.get('title')[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
