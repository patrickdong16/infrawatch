"""
采集服务
协调爬虫运行和数据存储
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from spiders import get_spider, list_spiders, OpenAISpider, AnthropicSpider, LambdaLabsSpider
from app.core.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class CollectionService:
    """
    采集服务
    
    职责:
    1. 根据配置调度爬虫
    2. 存储采集结果
    3. 计算派生指标
    """
    
    def __init__(self, repository=None):
        """
        初始化采集服务
        
        Args:
            repository: 数据仓库实例 (可选)
        """
        self.repository = repository
        
    async def collect_sector(self, sector_id: str) -> Dict[str, Any]:
        """
        采集单个板块数据
        
        Args:
            sector_id: 板块ID (B, C, E)
        """
        logger.info(f"[采集] 开始采集板块 {sector_id}")
        
        results = {
            "sector": sector_id,
            "started_at": datetime.utcnow().isoformat(),
            "providers": [],
            "total_records": 0,
            "errors": [],
        }
        
        # 获取板块配置
        sector_config = ConfigLoader.get_sector(sector_id)
        if not sector_config:
            results["errors"].append(f"板块配置不存在: {sector_id}")
            return results
        
        providers = sector_config.get("providers", [])
        
        for provider in providers:
            if not provider.get("enabled", True):
                continue
            
            provider_id = provider.get("id")
            spider_class_name = provider.get("spider_class", "").lower()
            
            try:
                # 获取爬虫实例
                spider = self._get_spider_for_provider(spider_class_name, provider)
                if not spider:
                    logger.warning(f"未找到爬虫: {spider_class_name}")
                    continue
                
                # 运行爬虫
                url = provider.get("pricing_url")
                records = await spider.run(url)
                
                # 转换为标准格式并存储
                stored_count = 0
                for record in records:
                    formatted = self._format_record(sector_id, provider_id, record)
                    
                    if self.repository:
                        await self.repository.save_metric(**formatted)
                        stored_count += 1
                
                results["providers"].append({
                    "provider_id": provider_id,
                    "records_collected": len(records),
                    "records_stored": stored_count,
                })
                results["total_records"] += len(records)
                
                logger.info(f"[采集] {provider_id} 完成: {len(records)} 条")
                
            except Exception as e:
                error_msg = f"{provider_id}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(f"[采集] 失败 - {error_msg}")
        
        results["completed_at"] = datetime.utcnow().isoformat()
        return results
    
    async def collect_all(self) -> Dict[str, Any]:
        """
        采集所有启用的板块
        """
        logger.info("[采集] 开始全量采集")
        
        results = {
            "started_at": datetime.utcnow().isoformat(),
            "sectors": {},
            "total_records": 0,
        }
        
        # 获取所有板块配置
        sectors = ConfigLoader.load_sectors()
        
        for sector_id, sector_config in sectors.items():
            if not sector_config.get("enabled", True):
                continue
            
            sector_result = await self.collect_sector(sector_id)
            results["sectors"][sector_id] = sector_result
            results["total_records"] += sector_result.get("total_records", 0)
        
        results["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"[采集] 全量采集完成: {results['total_records']} 条")
        return results
    
    def _get_spider_for_provider(self, spider_class: str, provider: Dict):
        """获取爬虫实例"""
        # 根据爬虫类名创建实例
        spider_map = {
            "openai_spider": OpenAISpider,
            "openai": OpenAISpider,
            "anthropic_spider": AnthropicSpider,
            "anthropic": AnthropicSpider,
            "lambda_labs_spider": LambdaLabsSpider,
            "lambdalabs": LambdaLabsSpider,
            "lambda_labs": LambdaLabsSpider,
        }
        
        spider_cls = spider_map.get(spider_class.lower().replace("-", "_"))
        if spider_cls:
            return spider_cls()
        
        return None
    
    def _format_record(self, sector_id: str, provider_id: str, record: Dict) -> Dict:
        """格式化记录为存储格式"""
        return {
            "sector": sector_id,
            "provider_id": provider_id,
            "sku_id": record.get("sku_id"),
            "metric_id": f"{provider_id}_{record.get('sku_id')}_{record.get('price_type', 'default')}",
            "value_data": {
                "price": record.get("price"),
                "currency": record.get("currency", "USD"),
                "price_type": record.get("price_type"),
                "unit": record.get("unit"),
                "specs": record.get("specs"),
            },
            "source_url": record.get("source_url"),
            "metadata": {
                "source": record.get("source", "spider"),
                "collected_at": datetime.utcnow().isoformat(),
            },
        }


async def run_collection(sector_id: Optional[str] = None):
    """
    运行采集任务
    
    可作为脚本直接运行或被 Celery 调用
    """
    service = CollectionService()
    
    if sector_id:
        result = await service.collect_sector(sector_id)
    else:
        result = await service.collect_all()
    
    return result


if __name__ == "__main__":
    # 直接运行测试
    import sys
    
    sector = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(run_collection(sector))
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
