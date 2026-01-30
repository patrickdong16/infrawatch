"""
TrendForce/DRAMeXchange 存储价格爬虫

从 DRAMeXchange 新闻页面抓取 HBM/DRAM 价格信号
"""

import re
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseSpider

logger = logging.getLogger(__name__)


class TrendForceSpider(BaseSpider):
    """
    TrendForce/DRAMeXchange 爬虫
    
    抓取内存市场新闻，提取价格信号
    """
    
    name: str = "trendforce_spider"
    
    # 数据源 URL
    SOURCES = {
        "market_view": "https://www.dramexchange.com/WeeklyResearch/MarketView",
        "daily": "https://www.dramexchange.com/Market/Daily",
        "enterprise_news": "https://www.dramexchange.com/WeeklyResearch/EnterpriseNews",
    }
    
    # 价格提取正则模式
    PRICE_PATTERNS = [
        # HBM 价格模式: "HBM3e prices increased by 15%"
        r"HBM\d?e?\s+(?:price[s]?|ASP)\s+(?:increase|rise|surge|jump|climb)[sd]?\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        r"HBM\d?e?\s+(?:price[s]?|ASP)\s+(?:decrease|drop|fall|decline)[sd]?\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        # DRAM 价格模式
        r"DRAM\s+(?:contract\s+)?(?:price[s]?|ASP)\s+(?:increase|rise|surge)[sd]?\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        r"DDR\d\s+(?:price[s]?|ASP)\s+(?:increase|rise)[sd]?\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        # 绝对价格: "$15.50 per GB"
        r"\$(\d+(?:\.\d+)?)\s*(?:per|\/)\s*(?:GB|chip|unit)",
        # 季度涨幅: "Q4 prices to increase 13-18% QoQ"
        r"Q\d\s+(?:price[s]?)\s+(?:to\s+)?(?:increase|rise)\s+(\d+)[-–](\d+)\s*%\s*QoQ",
    ]
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析页面内容，提取新闻文章"""
        soup = BeautifulSoup(content, "html.parser")
        articles = []
        
        # DRAMeXchange 页面结构：
        # - 标题: a.deepbluebold3
        # - 摘要: .BlogPostContent
        # - 日期: .BlogPostFooter 内的 span
        
        # 方法1: 通过标题链接查找文章
        title_links = soup.select("a.deepbluebold3")
        
        for title_elem in title_links[:20]:  # 限制数量
            try:
                # 提取标题
                title = title_elem.get_text(strip=True)
                
                # 提取链接
                link = title_elem.get("href", "")
                if link and not link.startswith("http"):
                    link = f"https://www.dramexchange.com{link}"
                
                # 找到父容器，然后查找摘要和日期
                parent = title_elem.find_parent("td") or title_elem.find_parent("div")
                
                # 提取日期 (在 BlogPostFooter 内)
                date_str = ""
                if parent:
                    footer = parent.find_next(class_="BlogPostFooter")
                    if footer:
                        date_span = footer.select_one(".title22 span") or footer.select_one("span")
                        if date_span:
                            date_str = date_span.get_text(strip=True)
                
                # 提取摘要 (BlogPostContent)
                summary = ""
                if parent:
                    content_div = parent.find_next(class_="BlogPostContent")
                    if content_div:
                        summary = content_div.get_text(strip=True)[:300]  # 限制长度
                
                if title:
                    articles.append({
                        "title": title,
                        "date": date_str,
                        "link": link,
                        "summary": summary,
                        "source": "DRAMeXchange",
                    })
            except Exception as e:
                logger.warning(f"解析文章失败: {e}")
                continue
        
        # 方法2: 备用 - 通过表格行查找
        if not articles:
            rows = soup.select("tr")
            for row in rows[:20]:
                try:
                    title_elem = row.select_one("a.deepbluebold3")
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://www.dramexchange.com{link}"
                    
                    articles.append({
                        "title": title,
                        "date": "",
                        "link": link,
                        "summary": "",
                        "source": "DRAMeXchange",
                    })
                except Exception as e:
                    continue
        
        logger.info(f"[trendforce_spider] 解析到 {len(articles)} 篇文章")
        return articles
    
    def extract_price_signals(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取价格信号"""
        signals = []
        
        for pattern in self.PRICE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    signal = {
                        "pattern": pattern[:50],
                        "match": match.group(0),
                        "values": match.groups(),
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                    
                    # 判断是涨还是跌
                    if any(word in match.group(0).lower() for word in ["increase", "rise", "surge", "jump", "climb"]):
                        signal["direction"] = "up"
                    elif any(word in match.group(0).lower() for word in ["decrease", "drop", "fall", "decline"]):
                        signal["direction"] = "down"
                    else:
                        signal["direction"] = "neutral"
                    
                    signals.append(signal)
                except Exception as e:
                    logger.warning(f"提取价格信号失败: {e}")
        
        return signals
    
    async def fetch_articles(self, source_key: str = "market_view") -> List[Dict[str, Any]]:
        """获取指定来源的文章"""
        url = self.SOURCES.get(source_key)
        if not url:
            logger.error(f"未知的数据源: {source_key}")
            return []
        
        return await self.run(url)
    
    async def fetch_all_sources(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有来源的文章"""
        results = {}
        for source_key in self.SOURCES:
            try:
                articles = await self.fetch_articles(source_key)
                results[source_key] = articles
                logger.info(f"[{source_key}] 获取 {len(articles)} 篇文章")
            except Exception as e:
                logger.error(f"[{source_key}] 获取失败: {e}")
                results[source_key] = []
        return results
    
    async def get_price_updates(self) -> List[Dict[str, Any]]:
        """获取价格更新信号（主入口）"""
        all_signals = []
        
        for source_key, url in self.SOURCES.items():
            try:
                articles = await self.run(url)
                
                for article in articles:
                    # 从标题和摘要中提取价格信号
                    text = f"{article.get('title', '')} {article.get('summary', '')}"
                    signals = self.extract_price_signals(text)
                    
                    for signal in signals:
                        signal["article_title"] = article.get("title")
                        signal["article_date"] = article.get("date")
                        signal["source"] = source_key
                        all_signals.append(signal)
                
            except Exception as e:
                logger.error(f"处理 {source_key} 失败: {e}")
        
        logger.info(f"共提取 {len(all_signals)} 个价格信号")
        return all_signals


# 便捷函数
async def fetch_memory_prices() -> List[Dict[str, Any]]:
    """获取内存价格信号"""
    spider = TrendForceSpider()
    return await spider.get_price_updates()
