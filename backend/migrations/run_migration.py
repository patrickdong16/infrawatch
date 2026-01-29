"""
数据库初始化脚本
用于从Python运行迁移
"""

import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration(database_url: str = None):
    """
    运行数据库迁移
    
    Args:
        database_url: 数据库连接URL (默认从环境变量获取)
    """
    # 获取数据库URL
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL 环境变量未设置")
    
    # 安全检查: 打印URL前30字符确认环境
    logger.info(f"[环境确认] 数据库URL前缀: {db_url[:30]}...")
    
    # 转换为异步URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # 创建引擎
    engine = create_async_engine(db_url, echo=True)
    
    # 读取迁移文件
    migrations_dir = Path(__file__).parent
    migration_file = migrations_dir / "001_initial.sql"
    
    if not migration_file.exists():
        raise FileNotFoundError(f"迁移文件不存在: {migration_file}")
    
    migration_sql = migration_file.read_text(encoding="utf-8")
    
    # 执行迁移
    async with engine.begin() as conn:
        logger.info("开始执行迁移...")
        
        # 分割SQL语句 (简单处理，实际可能需要更复杂的解析)
        statements = [s.strip() for s in migration_sql.split(";") if s.strip()]
        
        for stmt in statements:
            if stmt and not stmt.startswith("--"):
                try:
                    await conn.execute(text(stmt))
                except Exception as e:
                    logger.warning(f"语句执行警告: {e}")
        
        logger.info("迁移执行完成!")
    
    await engine.dispose()


async def check_tables(database_url: str = None):
    """检查表是否存在"""
    db_url = database_url or os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        logger.info(f"现有表: {tables}")
        
        required_tables = ['metric_records', 'signal_log', 'sector_configs', 'stage_history']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            logger.warning(f"缺少表: {missing}")
        else:
            logger.info("✓ 所有必需表都已存在")
    
    await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument("action", choices=["migrate", "check"], help="操作类型")
    parser.add_argument("--database-url", help="数据库URL")
    
    args = parser.parse_args()
    
    if args.action == "migrate":
        asyncio.run(run_migration(args.database_url))
    elif args.action == "check":
        asyncio.run(check_tables(args.database_url))
