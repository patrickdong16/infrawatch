"""
Celery 任务定义
定时采集和数据处理任务
"""

from celery import Celery
from celery.schedules import crontab
import asyncio
import os
import logging

# 配置 Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "infrawatch",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10分钟超时
)

# 定时任务
celery_app.conf.beat_schedule = {
    # 价格采集 - 每小时
    "collect-prices-hourly": {
        "task": "tasks.collect_all_prices",
        "schedule": crontab(minute=0),  # 每小时整点
    },
    # B板块 (模型API) - 每4小时
    "collect-sector-b": {
        "task": "tasks.collect_sector",
        "schedule": crontab(minute=0, hour="*/4"),
        "args": ("B",),
    },
    # C板块 (GPU云) - 每2小时
    "collect-sector-c": {
        "task": "tasks.collect_sector",
        "schedule": crontab(minute=30, hour="*/2"),
        "args": ("C",),
    },
    # E板块 (供应链) - 每天上午9点
    "collect-sector-e": {
        "task": "tasks.collect_sector",
        "schedule": crontab(minute=0, hour=9),
        "args": ("E",),
    },
    # 派生指标计算 - 每小时
    "calculate-derived-metrics": {
        "task": "tasks.calculate_derived_metrics",
        "schedule": crontab(minute=15),  # 每小时15分
    },
    # 信号检测 - 每小时
    "check-signals": {
        "task": "tasks.check_signals",
        "schedule": crontab(minute=20),  # 每小时20分
    },
    # 阶段评估 - 每天
    "evaluate-stage": {
        "task": "tasks.evaluate_stage",
        "schedule": crontab(minute=0, hour=0),  # 每天0点
    },
}

logger = logging.getLogger(__name__)


def run_async(coro):
    """在同步上下文中运行异步函数"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="tasks.collect_sector")
def collect_sector(sector_id: str):
    """
    采集单个板块数据
    """
    from app.services.collection_service import CollectionService
    
    logger.info(f"[Celery] 开始采集板块: {sector_id}")
    
    service = CollectionService()
    result = run_async(service.collect_sector(sector_id))
    
    logger.info(f"[Celery] 板块采集完成: {sector_id}, 记录数: {result.get('total_records', 0)}")
    return result


@celery_app.task(name="tasks.collect_all_prices")
def collect_all_prices():
    """
    采集所有价格数据
    """
    from app.services.collection_service import CollectionService
    
    logger.info("[Celery] 开始全量价格采集")
    
    service = CollectionService()
    result = run_async(service.collect_all())
    
    logger.info(f"[Celery] 全量采集完成, 总记录数: {result.get('total_records', 0)}")
    return result


@celery_app.task(name="tasks.calculate_derived_metrics")
def calculate_derived_metrics():
    """
    计算派生指标
    """
    logger.info("[Celery] 开始计算派生指标")
    
    # TODO: 实现派生指标计算
    # 1. 获取原始数据
    # 2. 根据 metrics/derived.yml 配置计算
    # 3. 存储结果
    
    return {"status": "completed", "message": "派生指标计算完成"}


@celery_app.task(name="tasks.check_signals")
def check_signals():
    """
    检测信号
    """
    logger.info("[Celery] 开始检测信号")
    
    # TODO: 实现信号检测
    # 1. 获取最新指标
    # 2. 根据 signals/rules.yml 检测
    # 3. 记录触发的信号
    
    return {"status": "completed", "signals_triggered": 0}


@celery_app.task(name="tasks.evaluate_stage")
def evaluate_stage():
    """
    评估当前周期阶段
    """
    logger.info("[Celery] 开始评估周期阶段")
    
    # TODO: 实现阶段评估
    # 1. 获取相关指标
    # 2. 根据 signals/stages.yml 评估
    # 3. 记录阶段变化
    
    return {"status": "completed", "stage": "S0", "confidence": 50}


# 手动触发任务的便捷函数
def trigger_collection(sector_id: str = None):
    """触发采集任务"""
    if sector_id:
        return collect_sector.delay(sector_id)
    else:
        return collect_all_prices.delay()
