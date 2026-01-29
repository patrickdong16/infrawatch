"""
配置相关 API 端点
提供前端动态加载配置的能力
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.core.config_loader import ConfigLoader
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


class ConfigResponse(BaseModel):
    """配置响应"""
    success: bool
    data: dict
    error: Optional[str] = None


@router.get("/dashboard")
async def get_dashboard_config():
    """
    获取仪表盘配置
    
    返回页面布局、导航、组件配置
    """
    try:
        ui_config = ConfigLoader.load_ui()
        
        # 构建仪表盘配置
        dashboard = ui_config.get("dashboard", {})
        
        return {
            "success": True,
            "data": {
                "pages": dashboard.get("pages", []),
                "navigation": dashboard.get("navigation", {}),
                "theme": dashboard.get("theme", {}),
            }
        }
    except Exception as e:
        logger.error(f"加载仪表盘配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sectors_config():
    """
    获取所有板块配置
    """
    try:
        sectors = ConfigLoader.load_sectors()
        return {
            "success": True,
            "data": sectors,
        }
    except Exception as e:
        logger.error(f"加载板块配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/{sector_id}")
async def get_sector_config(sector_id: str):
    """
    获取特定板块配置
    """
    try:
        sector = ConfigLoader.get_sector(sector_id)
        if not sector:
            raise HTTPException(status_code=404, detail=f"板块不存在: {sector_id}")
        
        return {
            "success": True,
            "data": sector,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载板块配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics_config():
    """
    获取指标配置
    """
    try:
        metrics = ConfigLoader.load_metrics()
        return {
            "success": True,
            "data": metrics,
        }
    except Exception as e:
        logger.error(f"加载指标配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_id}")
async def get_metric_definition(metric_id: str):
    """
    获取特定指标定义
    """
    try:
        metrics = ConfigLoader.load_metrics()
        metric_list = metrics.get("metrics", [])
        
        metric = next((m for m in metric_list if m.get("id") == metric_id), None)
        if not metric:
            raise HTTPException(status_code=404, detail=f"指标不存在: {metric_id}")
        
        return {
            "success": True,
            "data": metric,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载指标定义失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/rules")
async def get_signal_rules():
    """
    获取信号规则配置
    """
    try:
        signals = ConfigLoader.load_signals()
        return {
            "success": True,
            "data": signals.get("rules", {}),
        }
    except Exception as e:
        logger.error(f"加载信号规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/stages")
async def get_stage_definitions():
    """
    获取阶段定义配置
    """
    try:
        signals = ConfigLoader.load_signals()
        return {
            "success": True,
            "data": signals.get("stages", {}),
        }
    except Exception as e:
        logger.error(f"加载阶段定义失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
async def get_components_config():
    """
    获取组件配置
    """
    try:
        ui_config = ConfigLoader.load_ui()
        return {
            "success": True,
            "data": ui_config.get("components", {}),
        }
    except Exception as e:
        logger.error(f"加载组件配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_config():
    """
    重新加载配置
    
    用于热更新配置
    """
    try:
        ConfigLoader.reload()
        return {
            "success": True,
            "message": "配置已重新加载",
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version")
async def get_config_version():
    """
    获取配置版本信息
    """
    try:
        # 获取各配置的最后修改时间
        return {
            "success": True,
            "data": {
                "cached": ConfigLoader._cache is not None,
                "sectors_count": len(ConfigLoader.load_sectors()),
                "metrics_count": len(ConfigLoader.load_metrics().get("metrics", [])),
            }
        }
    except Exception as e:
        logger.error(f"获取配置版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
