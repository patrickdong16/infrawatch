"""
Price History Storage - 价格历史存储

使用 SQLite 进行 MVP 阶段的数据持久化。
支持:
- 价格历史记录
- 周/月/年同比计算
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "data" / "infrawatch.db"


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 价格历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            sector TEXT NOT NULL,
            price_type TEXT DEFAULT 'input',
            price REAL NOT NULL,
            unit TEXT,
            currency TEXT DEFAULT 'USD',
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            UNIQUE(provider, sku_id, price_type, recorded_at)
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_history_lookup 
        ON price_history(provider, sku_id, recorded_at)
    """)
    
    # 信号日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            metric_id TEXT,
            current_value REAL,
            previous_value REAL,
            change_percent REAL,
            sector TEXT,
            provider TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {DB_PATH}")


class PriceHistoryRepository:
    """价格历史仓库"""
    
    def __init__(self):
        init_db()
    
    def save_price(
        self,
        provider: str,
        sku_id: str,
        sector: str,
        price: float,
        price_type: str = "input",
        unit: str = None,
        metadata: Dict = None,
    ) -> int:
        """保存价格记录"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO price_history 
                (provider, sku_id, sector, price_type, price, unit, metadata, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                provider, sku_id, sector, price_type, price, unit,
                json.dumps(metadata) if metadata else None,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def save_prices_batch(self, prices: List[Dict]) -> int:
        """批量保存价格"""
        conn = get_db_connection()
        cursor = conn.cursor()
        count = 0
        
        try:
            for p in prices:
                provider = p.get("provider")
                sku_id = p.get("sku_id")
                
                # 确定板块
                sector = "C" if p.get("hourly_rate") else "B"
                
                # 保存输入价格
                if p.get("input_price"):
                    cursor.execute("""
                        INSERT OR IGNORE INTO price_history 
                        (provider, sku_id, sector, price_type, price, unit, recorded_at)
                        VALUES (?, ?, ?, 'input', ?, 'per_million_tokens', ?)
                    """, (provider, sku_id, sector, p["input_price"], datetime.utcnow().isoformat()))
                    count += 1
                
                # 保存输出价格
                if p.get("output_price"):
                    cursor.execute("""
                        INSERT OR IGNORE INTO price_history 
                        (provider, sku_id, sector, price_type, price, unit, recorded_at)
                        VALUES (?, ?, ?, 'output', ?, 'per_million_tokens', ?)
                    """, (provider, sku_id, sector, p["output_price"], datetime.utcnow().isoformat()))
                    count += 1
                
                # 保存小时价格 (GPU)
                if p.get("hourly_rate"):
                    cursor.execute("""
                        INSERT OR IGNORE INTO price_history 
                        (provider, sku_id, sector, price_type, price, unit, recorded_at)
                        VALUES (?, ?, ?, 'hourly', ?, 'per_hour', ?)
                    """, (provider, sku_id, sector, p["hourly_rate"], datetime.utcnow().isoformat()))
                    count += 1
            
            conn.commit()
            logger.info(f"批量保存 {count} 条价格记录")
            return count
        finally:
            conn.close()
    
    def get_latest_price(
        self,
        provider: str,
        sku_id: str,
        price_type: str = "input",
    ) -> Optional[Dict]:
        """获取最新价格"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM price_history 
                WHERE provider = ? AND sku_id = ? AND price_type = ?
                ORDER BY recorded_at DESC LIMIT 1
            """, (provider, sku_id, price_type))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_price_at(
        self,
        provider: str,
        sku_id: str,
        price_type: str,
        target_date: datetime,
        tolerance_days: int = 2,
    ) -> Optional[float]:
        """获取指定日期附近的价格"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        start = (target_date - timedelta(days=tolerance_days)).isoformat()
        end = (target_date + timedelta(days=tolerance_days)).isoformat()
        
        try:
            cursor.execute("""
                SELECT price FROM price_history 
                WHERE provider = ? AND sku_id = ? AND price_type = ?
                AND recorded_at BETWEEN ? AND ?
                ORDER BY ABS(julianday(recorded_at) - julianday(?))
                LIMIT 1
            """, (provider, sku_id, price_type, start, end, target_date.isoformat()))
            
            row = cursor.fetchone()
            return row["price"] if row else None
        finally:
            conn.close()
    
    def calculate_trends(
        self,
        provider: str,
        sku_id: str,
        price_type: str = "input",
        current_price: float = None,
    ) -> Dict[str, Optional[float]]:
        """
        计算趋势数据
        
        Returns:
            {
                "weekOverWeek": 周环比百分比,
                "monthOverMonth": 月环比百分比,
                "yearOverYear": 年同比百分比,
            }
        """
        now = datetime.utcnow()
        
        # 获取历史价格
        week_ago = self.get_price_at(provider, sku_id, price_type, now - timedelta(days=7))
        month_ago = self.get_price_at(provider, sku_id, price_type, now - timedelta(days=30))
        year_ago = self.get_price_at(provider, sku_id, price_type, now - timedelta(days=365))
        
        # 如果没有提供当前价格，从数据库获取
        if current_price is None:
            latest = self.get_latest_price(provider, sku_id, price_type)
            current_price = latest["price"] if latest else None
        
        if current_price is None:
            return {"weekOverWeek": None, "monthOverMonth": None, "yearOverYear": None}
        
        def calc_change(old_price: Optional[float]) -> Optional[float]:
            if old_price is None or old_price == 0:
                return None
            return round((current_price - old_price) / old_price * 100, 1)
        
        return {
            "weekOverWeek": calc_change(week_ago),
            "monthOverMonth": calc_change(month_ago),
            "yearOverYear": calc_change(year_ago),
        }
    
    def get_price_history(
        self,
        provider: str,
        sku_id: str,
        price_type: str = "input",
        days: int = 365,
    ) -> List[Dict]:
        """获取价格历史"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        try:
            cursor.execute("""
                SELECT price, recorded_at FROM price_history 
                WHERE provider = ? AND sku_id = ? AND price_type = ?
                AND recorded_at >= ?
                ORDER BY recorded_at ASC
            """, (provider, sku_id, price_type, start_date))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


# 全局仓库实例
_repo: Optional[PriceHistoryRepository] = None


def get_repository() -> PriceHistoryRepository:
    """获取全局仓库实例"""
    global _repo
    if _repo is None:
        _repo = PriceHistoryRepository()
    return _repo


def save_and_enrich_prices(prices: List[Dict]) -> List[Dict]:
    """
    保存价格并添加趋势数据
    
    用于替换 data.py 中的随机趋势生成
    """
    repo = get_repository()
    
    # 保存价格到数据库
    repo.save_prices_batch(prices)
    
    # 计算并添加趋势
    enriched = []
    for p in prices:
        item = p.copy()
        provider = p.get("provider")
        sku_id = p.get("sku_id")
        
        # 确定价格类型
        if p.get("hourly_rate"):
            price_type = "hourly"
            current_price = p["hourly_rate"]
        elif p.get("input_price"):
            price_type = "input"
            current_price = p["input_price"]
        else:
            enriched.append(item)
            continue
        
        # 计算趋势
        trends = repo.calculate_trends(provider, sku_id, price_type, current_price)
        item.update(trends)
        
        enriched.append(item)
    
    return enriched
