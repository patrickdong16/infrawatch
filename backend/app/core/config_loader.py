"""
配置加载器 - 核心模块
负责加载、缓存和验证YAML配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# 配置根目录
CONFIG_ROOT = Path(__file__).parent.parent.parent.parent / "config"


class ConfigError(Exception):
    """配置相关异常"""
    pass


class ConfigLoader:
    """配置加载器 - 支持热加载和缓存"""
    
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_timestamps: Dict[str, float] = {}
    
    @classmethod
    def load(cls, config_path: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 相对于config目录的路径，如 'sectors/sector_b.yml'
            force_reload: 是否强制重新加载
            
        Returns:
            解析后的配置字典
        """
        full_path = CONFIG_ROOT / config_path
        
        if not full_path.exists():
            raise ConfigError(f"配置文件不存在: {full_path}")
        
        # 检查缓存
        cache_key = str(full_path)
        file_mtime = full_path.stat().st_mtime
        
        if not force_reload and cache_key in cls._cache:
            if cls._cache_timestamps.get(cache_key) == file_mtime:
                return cls._cache[cache_key]
        
        # 加载并缓存
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            cls._cache[cache_key] = config
            cls._cache_timestamps[cache_key] = file_mtime
            logger.info(f"已加载配置: {config_path}")
            
            return config
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML解析错误 ({config_path}): {e}")
    
    @classmethod
    def load_sector(cls, sector_id: str) -> Dict[str, Any]:
        """加载板块配置"""
        return cls.load(f"sectors/sector_{sector_id.lower()}.yml")
    
    @classmethod
    def load_metrics(cls) -> Dict[str, Any]:
        """加载指标配置"""
        return cls.load("metrics/derived.yml")
    
    @classmethod
    def load_signal_rules(cls) -> Dict[str, Any]:
        """加载信号规则"""
        return cls.load("signals/rules.yml")
    
    @classmethod
    def load_stage_rules(cls) -> Dict[str, Any]:
        """加载阶段判定规则"""
        return cls.load("signals/stages.yml")
    
    @classmethod
    def load_ui_config(cls, page_id: Optional[str] = None) -> Dict[str, Any]:
        """加载UI配置"""
        config = cls.load("ui/dashboard.yml")
        
        if page_id:
            pages = config.get("pages", [])
            for page in pages:
                if page.get("id") == page_id:
                    return page
            raise ConfigError(f"页面不存在: {page_id}")
        
        return config
    
    @classmethod
    def reload_all(cls) -> None:
        """重新加载所有配置"""
        cls._cache.clear()
        cls._cache_timestamps.clear()
        logger.info("已清除所有配置缓存")
    
    @classmethod
    def get_all_sectors(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有启用的板块配置"""
        sectors = {}
        sector_dir = CONFIG_ROOT / "sectors"
        
        for yml_file in sector_dir.glob("sector_*.yml"):
            try:
                config = cls.load(f"sectors/{yml_file.name}")
                sector = config.get("sector", {})
                if sector.get("enabled", True):
                    sectors[sector.get("id")] = config
            except ConfigError as e:
                logger.warning(f"加载板块配置失败: {e}")
        
        return sectors
    
    @classmethod
    def get_providers_for_sector(cls, sector_id: str) -> list:
        """获取板块下的所有供应商"""
        config = cls.load_sector(sector_id)
        providers = config.get("providers", [])
        return [p for p in providers if p.get("enabled", True)]
    
    @classmethod
    def get_skus_for_provider(cls, sector_id: str, provider_id: str) -> list:
        """获取供应商下的所有SKU"""
        config = cls.load_sector(sector_id)
        skus = config.get("skus", {})
        return skus.get(provider_id, [])
    
    @classmethod
    def get_metric_definition(cls, metric_id: str) -> Optional[Dict[str, Any]]:
        """获取指标定义"""
        config = cls.load_metrics()
        for metric in config.get("metrics", []):
            if metric.get("id") == metric_id:
                return metric
        return None
    
    @classmethod
    def get_signal_rule(cls, signal_id: str) -> Optional[Dict[str, Any]]:
        """获取信号规则"""
        config = cls.load_signal_rules()
        for signal in config.get("signals", []):
            if signal.get("id") == signal_id:
                return signal
        return None


# 便捷函数
def get_config(path: str) -> Dict[str, Any]:
    """快捷加载配置"""
    return ConfigLoader.load(path)


def reload_configs() -> None:
    """重新加载所有配置"""
    ConfigLoader.reload_all()
