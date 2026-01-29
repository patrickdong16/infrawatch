"""
爬虫基类 - 提供通用爬虫功能
使用 httpx 进行异步请求，支持重试和超时
"""

import httpx
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_TIMEOUT = 10  # 10秒超时
DEFAULT_RETRIES = 3   # 3次重试
RETRY_DELAY = 1       # 重试间隔秒数


class BaseSpider(ABC):
    """
    爬虫基类
    
    所有具体爬虫需要继承此类并实现 parse 方法
    """
    
    name: str = "base_spider"
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def fetch(self, url: str, **kwargs) -> Optional[str]:
        """
        获取URL内容，带重试机制
        """
        headers = {**self.headers, **kwargs.get("headers", {})}
        
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
                    
            except httpx.TimeoutException:
                logger.warning(f"[{self.name}] 超时 (尝试 {attempt + 1}/{self.retries}): {url}")
            except httpx.HTTPStatusError as e:
                logger.warning(f"[{self.name}] HTTP错误 {e.response.status_code}: {url}")
                if e.response.status_code == 429:  # Rate limit
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1) * 2)
                elif e.response.status_code >= 500:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    return None  # 4xx 错误不重试
            except Exception as e:
                logger.error(f"[{self.name}] 请求失败: {e}")
            
            if attempt < self.retries - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        return None
    
    async def fetch_json(self, url: str, **kwargs) -> Optional[Dict]:
        """
        获取JSON数据
        """
        headers = {**self.headers, "Accept": "application/json", **kwargs.get("headers", {})}
        
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.json()
                    
            except Exception as e:
                logger.warning(f"[{self.name}] JSON请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.retries - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        return None
    
    @abstractmethod
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析页面内容
        
        子类必须实现此方法
        
        Returns:
            解析出的数据记录列表
        """
        pass
    
    async def run(self, url: str) -> List[Dict[str, Any]]:
        """
        执行爬虫
        """
        logger.info(f"[{self.name}] 开始采集: {url}")
        
        content = await self.fetch(url)
        if not content:
            logger.error(f"[{self.name}] 获取内容失败")
            return []
        
        try:
            results = await self.parse(content)
            logger.info(f"[{self.name}] 采集完成: {len(results)} 条记录")
            return results
        except Exception as e:
            logger.error(f"[{self.name}] 解析失败: {e}")
            return []


class APISpider(BaseSpider):
    """
    API爬虫基类
    
    用于直接调用API获取JSON数据的场景
    """
    
    async def parse(self, content: str) -> List[Dict[str, Any]]:
        """API爬虫不需要解析HTML"""
        return []
    
    @abstractmethod
    async def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        获取价格数据
        
        子类必须实现此方法
        """
        pass
    
    async def run(self, url: str = None) -> List[Dict[str, Any]]:
        """执行API爬虫"""
        return await self.fetch_prices()
