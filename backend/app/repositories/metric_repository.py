"""
通用指标数据仓库
使用JSONB存储动态字段，支持灵活的数据结构
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class MetricRepository:
    """
    通用指标数据访问层
    
    核心设计:
    - 使用 JSONB 存储动态字段，无需数据库迁移
    - 支持多种查询模式 (最新、历史、变化率)
    - 与配置系统解耦，纯数据操作
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_metric(
        self,
        sector: str,
        metric_id: str,
        value_data: Dict[str, Any],
        provider_id: Optional[str] = None,
        sku_id: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        recorded_at: Optional[datetime] = None,
    ) -> int:
        """
        保存指标数据
        
        Args:
            sector: 板块ID (A/B/C/D/E)
            metric_id: 指标ID
            value_data: 数据值 (JSONB)
            provider_id: 供应商ID (可选)
            sku_id: SKU ID (可选)
            source_url: 数据来源URL
            metadata: 额外元数据
            recorded_at: 记录时间 (默认当前时间)
        
        Returns:
            插入的记录ID
        """
        recorded_at = recorded_at or datetime.utcnow()
        metadata = metadata or {}
        
        query = text("""
            INSERT INTO metric_records 
            (recorded_at, sector, provider_id, sku_id, metric_id, value_data, source_url, metadata)
            VALUES (:recorded_at, :sector, :provider_id, :sku_id, :metric_id, :value_data::jsonb, :source_url, :metadata::jsonb)
            RETURNING id
        """)
        
        result = await self.session.execute(query, {
            "recorded_at": recorded_at,
            "sector": sector,
            "provider_id": provider_id,
            "sku_id": sku_id,
            "metric_id": metric_id,
            "value_data": value_data,
            "source_url": source_url,
            "metadata": metadata,
        })
        
        row = result.fetchone()
        await self.session.commit()
        
        return row[0] if row else 0
    
    async def save_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        批量保存指标数据
        
        Args:
            records: 记录列表
            
        Returns:
            插入的记录数
        """
        if not records:
            return 0
        
        # 使用批量插入
        query = text("""
            INSERT INTO metric_records 
            (recorded_at, sector, provider_id, sku_id, metric_id, value_data, source_url, metadata)
            VALUES (:recorded_at, :sector, :provider_id, :sku_id, :metric_id, :value_data::jsonb, :source_url, :metadata::jsonb)
        """)
        
        for record in records:
            record.setdefault("recorded_at", datetime.utcnow())
            record.setdefault("metadata", {})
            await self.session.execute(query, record)
        
        await self.session.commit()
        return len(records)
    
    async def get_latest(
        self,
        sector: Optional[str] = None,
        metric_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        sku_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取最新数据
        
        支持多种过滤条件
        """
        conditions = []
        params = {"limit": limit}
        
        if sector:
            conditions.append("sector = :sector")
            params["sector"] = sector
        
        if metric_id:
            conditions.append("metric_id = :metric_id")
            params["metric_id"] = metric_id
        
        if provider_id:
            conditions.append("provider_id = :provider_id")
            params["provider_id"] = provider_id
        
        if sku_id:
            conditions.append("sku_id = :sku_id")
            params["sku_id"] = sku_id
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 使用窗口函数获取每个组合的最新记录
        query = text(f"""
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY sector, provider_id, sku_id, metric_id 
                        ORDER BY recorded_at DESC
                    ) as rn
                FROM metric_records
                {where_clause}
            )
            SELECT id, recorded_at, sector, provider_id, sku_id, metric_id, 
                   value_data, source_url, metadata
            FROM ranked
            WHERE rn = 1
            ORDER BY recorded_at DESC
            LIMIT :limit
        """)
        
        result = await self.session.execute(query, params)
        rows = result.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    async def get_history(
        self,
        metric_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        provider_id: Optional[str] = None,
        sku_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        获取历史数据
        """
        end_date = end_date or datetime.utcnow()
        
        conditions = [
            "metric_id = :metric_id",
            "recorded_at >= :start_date",
            "recorded_at <= :end_date",
        ]
        params = {
            "metric_id": metric_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        }
        
        if provider_id:
            conditions.append("provider_id = :provider_id")
            params["provider_id"] = provider_id
        
        if sku_id:
            conditions.append("sku_id = :sku_id")
            params["sku_id"] = sku_id
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        query = text(f"""
            SELECT id, recorded_at, sector, provider_id, sku_id, metric_id, 
                   value_data, source_url, metadata
            FROM metric_records
            {where_clause}
            ORDER BY recorded_at ASC
            LIMIT :limit
        """)
        
        result = await self.session.execute(query, params)
        rows = result.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    async def get_change(
        self,
        metric_id: str,
        period: str = "wow",
        provider_id: Optional[str] = None,
        sku_id: Optional[str] = None,
    ) -> Optional[float]:
        """
        计算变化率
        
        Args:
            metric_id: 指标ID
            period: 周期类型 (wow=周环比, mom=月环比, qoq=季度环比)
            provider_id: 供应商ID
            sku_id: SKU ID
            
        Returns:
            变化率 (小数形式，如 0.1 表示 10%)
        """
        # 根据周期计算日期
        period_days = {
            "wow": 7,
            "mom": 30,
            "qoq": 90,
        }
        
        days = period_days.get(period, 7)
        now = datetime.utcnow()
        prev_date = now - timedelta(days=days)
        
        # 获取当前值和之前的值
        conditions = ["metric_id = :metric_id"]
        params = {"metric_id": metric_id}
        
        if provider_id:
            conditions.append("provider_id = :provider_id")
            params["provider_id"] = provider_id
        
        if sku_id:
            conditions.append("sku_id = :sku_id")
            params["sku_id"] = sku_id
        
        where_clause = " AND ".join(conditions)
        
        # 获取最新值
        query_current = text(f"""
            SELECT value_data->>'price' as price
            FROM metric_records
            WHERE {where_clause}
            ORDER BY recorded_at DESC
            LIMIT 1
        """)
        
        # 获取之前的值
        query_prev = text(f"""
            SELECT value_data->>'price' as price
            FROM metric_records
            WHERE {where_clause} AND recorded_at <= :prev_date
            ORDER BY recorded_at DESC
            LIMIT 1
        """)
        
        params["prev_date"] = prev_date
        
        result_current = await self.session.execute(query_current, params)
        result_prev = await self.session.execute(query_prev, params)
        
        row_current = result_current.fetchone()
        row_prev = result_prev.fetchone()
        
        if not row_current or not row_prev:
            return None
        
        try:
            current_price = float(row_current[0])
            prev_price = float(row_prev[0])
            
            if prev_price == 0:
                return None
            
            return (current_price - prev_price) / prev_price
        except (ValueError, TypeError):
            return None
    
    async def get_price_with_changes(
        self,
        sector: str,
        include_changes: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取价格及其变化率
        
        Args:
            sector: 板块ID
            include_changes: 要计算的变化率周期 ['wow', 'mom', 'qoq']
        """
        include_changes = include_changes or ["wow", "mom"]
        
        # 获取最新价格
        latest = await self.get_latest(sector=sector)
        
        # 为每条记录计算变化率
        for record in latest:
            record["changes"] = {}
            for period in include_changes:
                change = await self.get_change(
                    metric_id=record["metric_id"],
                    period=period,
                    provider_id=record.get("provider_id"),
                    sku_id=record.get("sku_id"),
                )
                record["changes"][period] = change
        
        return latest
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        return {
            "id": row[0],
            "recorded_at": row[1].isoformat() if row[1] else None,
            "sector": row[2],
            "provider_id": row[3],
            "sku_id": row[4],
            "metric_id": row[5],
            "value_data": row[6],
            "source_url": row[7],
            "metadata": row[8],
        }
