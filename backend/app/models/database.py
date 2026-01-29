"""
数据库迁移: 创建核心表
支持 TimescaleDB 时序扩展

前置条件:
- PostgreSQL 15+
- TimescaleDB 扩展 (可选，用于时序优化)
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Index, ForeignKey,
    UniqueConstraint, CheckConstraint, MetaData
)
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# 信号严重程度枚举
severity_enum = ENUM('info', 'warning', 'critical', name='severity_level', create_type=True)


class MetricRecord(Base):
    """
    指标记录表 - 使用JSONB存储动态字段
    
    设计要点:
    1. value_data 使用 JSONB，无需迁移即可扩展字段
    2. 复合索引支持多维查询
    3. 支持 TimescaleDB hypertable (可选)
    """
    __tablename__ = 'metric_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 分类维度
    sector = Column(String(10), nullable=False, index=True)  # A/B/C/D/E
    provider_id = Column(String(50), nullable=True, index=True)
    sku_id = Column(String(100), nullable=True)
    metric_id = Column(String(100), nullable=False, index=True)
    
    # 数据值 (JSONB)
    value_data = Column(JSONB, nullable=False)
    
    # 元数据
    source_url = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True, default={})
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # 复合索引用于常见查询模式
        Index('ix_metric_sector_time', 'sector', 'recorded_at'),
        Index('ix_metric_provider_sku', 'provider_id', 'sku_id'),
        Index('ix_metric_metric_time', 'metric_id', 'recorded_at'),
        # JSONB GIN 索引用于JSON查询
        Index('ix_metric_value_data', 'value_data', postgresql_using='gin'),
    )


class SignalLog(Base):
    """
    信号日志表 - 记录触发的信号
    """
    __tablename__ = 'signal_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 信号类型
    signal_type = Column(String(50), nullable=False, index=True)  # price_move, threshold, etc.
    signal_rule_id = Column(String(100), nullable=False)
    
    # 严重程度
    severity = Column(severity_enum, nullable=False, default='info')
    
    # 描述
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 关联指标
    metric_id = Column(String(100), nullable=True)
    sector = Column(String(10), nullable=True)
    
    # 触发详情 (JSONB)
    trigger_data = Column(JSONB, nullable=True)  # 包含 value, threshold, condition 等
    
    # 状态
    acknowledged = Column(DateTime, nullable=True)  # 确认时间
    resolved = Column(DateTime, nullable=True)  # 解决时间
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_signal_type_time', 'signal_type', 'triggered_at'),
        Index('ix_signal_severity', 'severity'),
    )


class SectorConfig(Base):
    """
    板块配置缓存表 - 用于配置版本管理
    """
    __tablename__ = 'sector_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector = Column(String(10), nullable=False, unique=True)
    config_version = Column(String(50), nullable=False)
    config_data = Column(JSONB, nullable=False)
    
    # 审计
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)


class StageHistory(Base):
    """
    阶段历史表 - 记录周期阶段变化
    """
    __tablename__ = 'stage_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    stage = Column(String(5), nullable=False)  # S0, S1, S2, S3
    confidence = Column(Integer, nullable=False)  # 0-100
    
    # 触发条件 (JSONB)
    trigger_conditions = Column(JSONB, nullable=True)
    
    # 描述
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ Alembic 迁移脚本模板 ============

MIGRATION_UP = """
-- 创建扩展 (如果需要)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建枚举类型
DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('info', 'warning', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建 metric_records 表
CREATE TABLE IF NOT EXISTS metric_records (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    sector VARCHAR(10) NOT NULL,
    provider_id VARCHAR(50),
    sku_id VARCHAR(100),
    metric_id VARCHAR(100) NOT NULL,
    value_data JSONB NOT NULL,
    source_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_metric_records_recorded_at ON metric_records (recorded_at);
CREATE INDEX IF NOT EXISTS ix_metric_records_sector ON metric_records (sector);
CREATE INDEX IF NOT EXISTS ix_metric_records_metric_id ON metric_records (metric_id);
CREATE INDEX IF NOT EXISTS ix_metric_sector_time ON metric_records (sector, recorded_at);
CREATE INDEX IF NOT EXISTS ix_metric_provider_sku ON metric_records (provider_id, sku_id);
CREATE INDEX IF NOT EXISTS ix_metric_value_data ON metric_records USING GIN (value_data);

-- 可选: 转换为 TimescaleDB hypertable (需要先安装 TimescaleDB)
-- SELECT create_hypertable('metric_records', 'recorded_at', if_not_exists => TRUE);

-- 创建 signal_log 表
CREATE TABLE IF NOT EXISTS signal_log (
    id SERIAL PRIMARY KEY,
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    signal_type VARCHAR(50) NOT NULL,
    signal_rule_id VARCHAR(100) NOT NULL,
    severity severity_level NOT NULL DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    metric_id VARCHAR(100),
    sector VARCHAR(10),
    trigger_data JSONB,
    acknowledged TIMESTAMP,
    resolved TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_signal_log_triggered_at ON signal_log (triggered_at);
CREATE INDEX IF NOT EXISTS ix_signal_log_type_time ON signal_log (signal_type, triggered_at);
CREATE INDEX IF NOT EXISTS ix_signal_log_severity ON signal_log (severity);

-- 创建 sector_configs 表
CREATE TABLE IF NOT EXISTS sector_configs (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(10) NOT NULL UNIQUE,
    config_version VARCHAR(50) NOT NULL,
    config_data JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- 创建 stage_history 表
CREATE TABLE IF NOT EXISTS stage_history (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    stage VARCHAR(5) NOT NULL,
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    trigger_conditions JSONB,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stage_history_recorded_at ON stage_history (recorded_at);
"""

MIGRATION_DOWN = """
DROP TABLE IF EXISTS stage_history;
DROP TABLE IF EXISTS sector_configs;
DROP TABLE IF EXISTS signal_log;
DROP TABLE IF EXISTS metric_records;
DROP TYPE IF EXISTS severity_level;
"""


def get_migration_sql(direction: str = 'up') -> str:
    """获取迁移SQL"""
    return MIGRATION_UP if direction == 'up' else MIGRATION_DOWN
