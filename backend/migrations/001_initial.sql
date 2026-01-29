-- InfraWatch 初始化迁移
-- 运行方式: psql -d infrawatch -f 001_initial.sql

-- ============ 扩展 ============
-- 如果安装了 TimescaleDB，取消下面的注释
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============ 枚举类型 ============
DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('info', 'warning', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============ 核心表 ============

-- 1. 指标记录表 (使用 JSONB 存储动态字段)
CREATE TABLE IF NOT EXISTS metric_records (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- 分类维度
    sector VARCHAR(10) NOT NULL,          -- A/B/C/D/E
    provider_id VARCHAR(50),              -- 供应商ID
    sku_id VARCHAR(100),                  -- SKU ID
    metric_id VARCHAR(100) NOT NULL,      -- 指标ID
    
    -- 数据值 (JSONB, 无需迁移即可扩展)
    value_data JSONB NOT NULL,
    
    -- 元数据
    source_url TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- 审计
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS ix_metric_records_recorded_at ON metric_records (recorded_at);
CREATE INDEX IF NOT EXISTS ix_metric_records_sector ON metric_records (sector);
CREATE INDEX IF NOT EXISTS ix_metric_records_metric_id ON metric_records (metric_id);
CREATE INDEX IF NOT EXISTS ix_metric_records_provider_id ON metric_records (provider_id);
CREATE INDEX IF NOT EXISTS ix_metric_sector_time ON metric_records (sector, recorded_at DESC);
CREATE INDEX IF NOT EXISTS ix_metric_provider_sku ON metric_records (provider_id, sku_id);
CREATE INDEX IF NOT EXISTS ix_metric_metric_time ON metric_records (metric_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS ix_metric_value_data ON metric_records USING GIN (value_data);

-- 可选: TimescaleDB hypertable (需要先安装 TimescaleDB)
-- SELECT create_hypertable('metric_records', 'recorded_at', if_not_exists => TRUE);

-- 2. 信号日志表
CREATE TABLE IF NOT EXISTS signal_log (
    id SERIAL PRIMARY KEY,
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- 信号类型
    signal_type VARCHAR(50) NOT NULL,     -- price_move, threshold, adoption 等
    signal_rule_id VARCHAR(100) NOT NULL, -- 对应 rules.yml 中的 id
    severity severity_level NOT NULL DEFAULT 'info',
    
    -- 描述
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 关联
    metric_id VARCHAR(100),
    sector VARCHAR(10),
    
    -- 触发详情
    trigger_data JSONB,                   -- value, threshold, condition 等
    
    -- 状态
    acknowledged TIMESTAMP,               -- 确认时间
    resolved TIMESTAMP,                   -- 解决时间
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_signal_log_triggered_at ON signal_log (triggered_at DESC);
CREATE INDEX IF NOT EXISTS ix_signal_log_type ON signal_log (signal_type);
CREATE INDEX IF NOT EXISTS ix_signal_log_type_time ON signal_log (signal_type, triggered_at DESC);
CREATE INDEX IF NOT EXISTS ix_signal_log_severity ON signal_log (severity);
CREATE INDEX IF NOT EXISTS ix_signal_log_unresolved ON signal_log (triggered_at) WHERE resolved IS NULL;

-- 3. 板块配置表 (配置版本管理)
CREATE TABLE IF NOT EXISTS sector_configs (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(10) NOT NULL UNIQUE,
    config_version VARCHAR(50) NOT NULL,
    config_data JSONB NOT NULL,
    
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- 4. 阶段历史表
CREATE TABLE IF NOT EXISTS stage_history (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    stage VARCHAR(5) NOT NULL,            -- S0, S1, S2, S3
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    
    -- 触发条件详情
    trigger_conditions JSONB,
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stage_history_recorded_at ON stage_history (recorded_at DESC);

-- ============ 初始数据 ============

-- 插入初始阶段记录
INSERT INTO stage_history (stage, confidence, description)
VALUES ('S0', 50, '系统初始化 - 默认基建期')
ON CONFLICT DO NOTHING;

-- ============ 完成 ============
SELECT 'Migration 001_initial completed successfully' AS status;
