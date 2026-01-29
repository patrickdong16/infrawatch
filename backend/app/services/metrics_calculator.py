"""
派生指标计算器
根据 config/metrics/derived.yml 计算派生指标
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.core.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """指标值"""
    metric_id: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCalculator:
    """
    派生指标计算器
    
    支持的计算类型:
    - weighted_average: 加权平均
    - ratio: 比率
    - change_rate: 变化率
    - index: 指数
    """
    
    def __init__(self, repository=None):
        self.repository = repository
        self._load_metric_definitions()
    
    def _load_metric_definitions(self):
        """加载指标定义"""
        try:
            self.metrics_config = ConfigLoader.load_metrics()
            self.derived_metrics = self.metrics_config.get("derived", [])
        except Exception as e:
            logger.warning(f"加载指标配置失败: {e}")
            self.derived_metrics = []
    
    async def calculate_all(self) -> List[MetricValue]:
        """计算所有派生指标"""
        results = []
        
        for metric_def in self.derived_metrics:
            try:
                value = await self.calculate_metric(metric_def)
                if value is not None:
                    results.append(value)
            except Exception as e:
                logger.error(f"计算指标失败 {metric_def.get('id')}: {e}")
        
        return results
    
    async def calculate_metric(self, metric_def: Dict) -> Optional[MetricValue]:
        """计算单个派生指标"""
        metric_id = metric_def.get("id")
        calc_type = metric_def.get("type")
        
        logger.info(f"计算指标: {metric_id} (类型: {calc_type})")
        
        if calc_type == "weighted_average":
            return await self._calc_weighted_average(metric_def)
        elif calc_type == "ratio":
            return await self._calc_ratio(metric_def)
        elif calc_type == "change_rate":
            return await self._calc_change_rate(metric_def)
        elif calc_type == "index":
            return await self._calc_index(metric_def)
        else:
            logger.warning(f"未知计算类型: {calc_type}")
            return None
    
    async def _calc_weighted_average(self, metric_def: Dict) -> Optional[MetricValue]:
        """
        计算加权平均
        
        配置示例:
        {
            "id": "inference_price_index",
            "type": "weighted_average",
            "sources": [
                {"metric": "openai_gpt4o_input", "weight": 0.4},
                {"metric": "anthropic_claude_sonnet_input", "weight": 0.3},
                {"metric": "google_gemini_pro_input", "weight": 0.3}
            ]
        }
        """
        sources = metric_def.get("sources", [])
        if not sources:
            return None
        
        total_weight = 0
        weighted_sum = 0
        
        for source in sources:
            metric_id = source.get("metric")
            weight = source.get("weight", 1.0)
            
            # 获取源指标值
            value = await self._get_latest_value(metric_id)
            if value is not None:
                weighted_sum += value * weight
                total_weight += weight
        
        if total_weight == 0:
            return None
        
        result = weighted_sum / total_weight
        
        return MetricValue(
            metric_id=metric_def.get("id"),
            value=round(result, 4),
            timestamp=datetime.utcnow(),
            metadata={"type": "weighted_average", "sources_count": len(sources)}
        )
    
    async def _calc_ratio(self, metric_def: Dict) -> Optional[MetricValue]:
        """
        计算比率
        
        配置示例:
        {
            "id": "price_performance_ratio",
            "type": "ratio",
            "numerator": "gpt4o_price",
            "denominator": "gpt35_price"
        }
        """
        numerator_id = metric_def.get("numerator")
        denominator_id = metric_def.get("denominator")
        
        numerator = await self._get_latest_value(numerator_id)
        denominator = await self._get_latest_value(denominator_id)
        
        if numerator is None or denominator is None or denominator == 0:
            return None
        
        result = numerator / denominator
        
        return MetricValue(
            metric_id=metric_def.get("id"),
            value=round(result, 4),
            timestamp=datetime.utcnow(),
            metadata={"type": "ratio"}
        )
    
    async def _calc_change_rate(self, metric_def: Dict) -> Optional[MetricValue]:
        """
        计算变化率
        
        配置示例:
        {
            "id": "gpt4o_price_change_7d",
            "type": "change_rate",
            "source": "openai_gpt4o_input",
            "period_days": 7
        }
        """
        source_id = metric_def.get("source")
        period_days = metric_def.get("period_days", 7)
        
        current = await self._get_latest_value(source_id)
        previous = await self._get_value_at(source_id, days_ago=period_days)
        
        if current is None or previous is None or previous == 0:
            return None
        
        change_rate = (current - previous) / previous * 100  # 百分比
        
        return MetricValue(
            metric_id=metric_def.get("id"),
            value=round(change_rate, 2),
            timestamp=datetime.utcnow(),
            metadata={"type": "change_rate", "period_days": period_days, "unit": "percent"}
        )
    
    async def _calc_index(self, metric_def: Dict) -> Optional[MetricValue]:
        """
        计算指数 (基于基准值)
        
        配置示例:
        {
            "id": "gpu_price_index",
            "type": "index",
            "source": "h100_hourly_price",
            "base_value": 3.00,
            "base_date": "2024-01-01"
        }
        """
        source_id = metric_def.get("source")
        base_value = metric_def.get("base_value", 100)
        
        current = await self._get_latest_value(source_id)
        
        if current is None or base_value == 0:
            return None
        
        index = (current / base_value) * 100
        
        return MetricValue(
            metric_id=metric_def.get("id"),
            value=round(index, 2),
            timestamp=datetime.utcnow(),
            metadata={"type": "index", "base_value": base_value}
        )
    
    async def _get_latest_value(self, metric_id: str) -> Optional[float]:
        """获取指标最新值"""
        if self.repository:
            try:
                records = await self.repository.get_latest(metric_id=metric_id, limit=1)
                if records:
                    value_data = records[0].get("value_data", {})
                    return value_data.get("price") or value_data.get("value")
            except Exception as e:
                logger.error(f"获取指标值失败 {metric_id}: {e}")
        
        # 模拟数据 (用于测试)
        mock_values = {
            "openai_gpt4o_input": 2.50,
            "openai_gpt4o_output": 10.00,
            "anthropic_claude_sonnet_input": 3.00,
            "anthropic_claude_sonnet_output": 15.00,
            "h100_hourly_price": 2.49,
            "a100_hourly_price": 1.29,
        }
        return mock_values.get(metric_id)
    
    async def _get_value_at(self, metric_id: str, days_ago: int) -> Optional[float]:
        """获取指定天数前的值"""
        if self.repository:
            try:
                target_date = datetime.utcnow() - timedelta(days=days_ago)
                records = await self.repository.get_history(
                    metric_id=metric_id,
                    start_date=target_date - timedelta(days=1),
                    end_date=target_date + timedelta(days=1),
                    limit=1
                )
                if records:
                    value_data = records[0].get("value_data", {})
                    return value_data.get("price") or value_data.get("value")
            except Exception as e:
                logger.error(f"获取历史值失败 {metric_id}: {e}")
        
        # 模拟: 返回当前值的95% (模拟价格下降)
        current = await self._get_latest_value(metric_id)
        if current:
            return current * 1.05  # 假设7天前价格高5%
        return None


# 预定义的派生指标
STANDARD_DERIVED_METRICS = [
    {
        "id": "inference_price_index",
        "name": "推理价格指数",
        "type": "weighted_average",
        "sources": [
            {"metric": "openai_gpt4o_input", "weight": 0.4},
            {"metric": "anthropic_claude_sonnet_input", "weight": 0.35},
        ],
    },
    {
        "id": "gpu_hourly_index",
        "name": "GPU小时价格指数",
        "type": "weighted_average",
        "sources": [
            {"metric": "h100_hourly_price", "weight": 0.6},
            {"metric": "a100_hourly_price", "weight": 0.4},
        ],
    },
    {
        "id": "price_trend_7d",
        "name": "7日价格趋势",
        "type": "change_rate",
        "source": "inference_price_index",
        "period_days": 7,
    },
]


async def calculate_derived_metrics(repository=None) -> List[Dict]:
    """
    计算所有派生指标
    
    便捷函数，可被 Celery 任务调用
    """
    calculator = MetricsCalculator(repository)
    
    # 如果没有配置，使用标准定义
    if not calculator.derived_metrics:
        calculator.derived_metrics = STANDARD_DERIVED_METRICS
    
    results = await calculator.calculate_all()
    
    return [
        {
            "metric_id": r.metric_id,
            "value": r.value,
            "timestamp": r.timestamp.isoformat(),
            "metadata": r.metadata,
        }
        for r in results
    ]


if __name__ == "__main__":
    import asyncio
    import json
    
    async def test():
        results = await calculate_derived_metrics()
        print("派生指标计算结果:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
