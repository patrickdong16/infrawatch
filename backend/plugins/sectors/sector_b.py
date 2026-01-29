"""
B板块插件: 模型API价格
负责采集和计算模型API定价数据
"""

from typing import Any, Dict, List
from datetime import datetime
import logging

from plugins.base import SectorPlugin, SpiderMixin
from app.core.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class SectorBPlugin(SectorPlugin, SpiderMixin):
    """
    B板块插件
    
    负责:
    1. 采集各模型厂商的API定价
    2. 计算价格指数和中国折扣率
    """
    
    sector_id = "B"
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        采集所有启用的供应商的价格数据
        """
        results = []
        
        for provider in self.providers:
            provider_id = provider.get("id")
            spider_class = provider.get("spider_class")
            
            if not spider_class:
                logger.warning(f"供应商 {provider_id} 未配置爬虫类")
                continue
            
            try:
                logger.info(f"[{self.sector_id}] 采集 {provider_id}...")
                records = await self.run_spider(spider_class, provider)
                
                # 转换为标准格式
                for record in records:
                    results.append({
                        "sector": self.sector_id,
                        "provider_id": provider_id,
                        "sku_id": record.get("sku_id"),
                        "metric_id": f"{provider_id}_{record.get('sku_id')}_{record.get('price_type', 'default')}",
                        "value_data": {
                            "price": record.get("price"),
                            "currency": record.get("currency", "USD"),
                            "price_type": record.get("price_type"),
                        },
                        "source_url": provider.get("pricing_url"),
                        "recorded_at": datetime.utcnow(),
                    })
                
                logger.info(f"[{self.sector_id}] {provider_id} 采集完成: {len(records)} 条")
                
            except Exception as e:
                logger.error(f"[{self.sector_id}] 采集 {provider_id} 失败: {e}")
        
        return results
    
    async def calculate_derived(self) -> List[Dict[str, Any]]:
        """
        计算派生指标
        """
        results = []
        metrics_config = ConfigLoader.load_metrics()
        
        for metric in metrics_config.get("metrics", []):
            if metric.get("sector") != self.sector_id:
                continue
            
            metric_id = metric.get("id")
            metric_type = metric.get("type")
            
            try:
                if metric_type == "weighted_average":
                    value = await self._calculate_weighted_average(metric)
                elif metric_type == "ratio":
                    value = await self._calculate_ratio(metric)
                elif metric_type == "change_rate":
                    value = await self._calculate_change_rate(metric)
                else:
                    logger.warning(f"未知的指标类型: {metric_type}")
                    continue
                
                if value is not None:
                    results.append({
                        "sector": self.sector_id,
                        "metric_id": metric_id,
                        "value_data": {
                            "value": value,
                            "unit": metric.get("unit"),
                            "calculated_at": datetime.utcnow().isoformat(),
                        },
                        "recorded_at": datetime.utcnow(),
                    })
                    
            except Exception as e:
                logger.error(f"计算 {metric_id} 失败: {e}")
        
        return results
    
    async def _calculate_weighted_average(self, metric: Dict) -> float:
        """计算加权平均"""
        inputs = metric.get("inputs", [])
        total_weight = 0
        weighted_sum = 0
        
        for input_def in inputs:
            source = input_def.get("source", {})
            weight = input_def.get("weight", 0)
            
            # 从数据库获取价格 (这里简化处理)
            # 实际实现需要注入 MetricRepository
            price = await self._get_latest_price(
                source.get("provider"),
                source.get("sku"),
                source.get("price_type"),
            )
            
            if price is not None:
                weighted_sum += price * weight
                total_weight += weight
        
        if total_weight == 0:
            return None
        
        return weighted_sum / total_weight
    
    async def _calculate_ratio(self, metric: Dict) -> float:
        """计算比率"""
        inputs = metric.get("inputs", {})
        
        # 获取分子和分母的值
        values = {}
        for key, source in inputs.items():
            price = await self._get_latest_price(
                source.get("provider"),
                source.get("sku"),
                source.get("price_type"),
            )
            values[key] = price
        
        # 执行公式 (简化版本)
        formula = metric.get("formula", "")
        
        try:
            # 安全的公式计算
            result = eval(formula, {"__builtins__": {}}, values)
            return result
        except Exception as e:
            logger.error(f"公式计算失败: {formula}, 值: {values}, 错误: {e}")
            return None
    
    async def _calculate_change_rate(self, metric: Dict) -> float:
        """计算变化率"""
        # 需要获取 base_metric 的历史数据
        # 这里简化处理
        return None
    
    async def _get_latest_price(
        self, 
        provider: str, 
        sku: str, 
        price_type: str
    ) -> float:
        """
        获取最新价格
        
        注意: 实际实现需要注入 MetricRepository
        这里作为示例返回 None
        """
        # TODO: 注入 MetricRepository 实现真实查询
        return None
