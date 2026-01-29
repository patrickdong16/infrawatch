"""
插件注册表
自动发现、注册和管理板块插件
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type
import logging

from plugins.base import SectorPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    插件注册表
    
    支持:
    - 自动发现插件
    - 按板块ID获取插件
    - 获取所有启用的插件
    """
    
    _plugins: Dict[str, SectorPlugin] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, plugin: SectorPlugin) -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
        """
        sector_id = plugin.sector_id
        if sector_id in cls._plugins:
            logger.warning(f"插件 {sector_id} 已存在，将被覆盖")
        
        cls._plugins[sector_id] = plugin
        logger.info(f"已注册插件: {sector_id} ({plugin.__class__.__name__})")
    
    @classmethod
    def get(cls, sector_id: str) -> Optional[SectorPlugin]:
        """
        获取指定板块的插件
        
        Args:
            sector_id: 板块ID (A/B/C/D/E)
        """
        cls._ensure_initialized()
        return cls._plugins.get(sector_id.upper())
    
    @classmethod
    def get_all(cls) -> Dict[str, SectorPlugin]:
        """获取所有已注册的插件"""
        cls._ensure_initialized()
        return cls._plugins.copy()
    
    @classmethod
    def get_enabled(cls) -> List[SectorPlugin]:
        """获取所有启用的插件"""
        cls._ensure_initialized()
        return [p for p in cls._plugins.values() if p.is_enabled()]
    
    @classmethod
    def auto_discover(cls) -> None:
        """
        自动发现并注册插件
        
        扫描 plugins/sectors 目录下的所有模块
        """
        plugins_dir = Path(__file__).parent / "sectors"
        
        if not plugins_dir.exists():
            logger.warning(f"插件目录不存在: {plugins_dir}")
            return
        
        for module_info in pkgutil.iter_modules([str(plugins_dir)]):
            if module_info.name.startswith("_"):
                continue
            
            try:
                module = importlib.import_module(f"plugins.sectors.{module_info.name}")
                
                # 查找 SectorPlugin 子类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type) and
                        issubclass(attr, SectorPlugin) and
                        attr is not SectorPlugin and
                        hasattr(attr, 'sector_id') and
                        attr.sector_id
                    ):
                        try:
                            plugin = attr()
                            cls.register(plugin)
                        except Exception as e:
                            logger.error(f"实例化插件失败 {attr_name}: {e}")
            
            except Exception as e:
                logger.error(f"加载模块失败 {module_info.name}: {e}")
        
        cls._initialized = True
        logger.info(f"自动发现完成，共注册 {len(cls._plugins)} 个插件")
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """确保已初始化"""
        if not cls._initialized:
            cls.auto_discover()
    
    @classmethod
    def reset(cls) -> None:
        """重置注册表 (主要用于测试)"""
        cls._plugins.clear()
        cls._initialized = False
    
    @classmethod
    async def run_all(cls) -> Dict[str, Dict]:
        """
        运行所有启用的插件
        
        Returns:
            每个插件的执行结果
        """
        results = {}
        
        for plugin in cls.get_enabled():
            try:
                results[plugin.sector_id] = await plugin.run_full_cycle()
            except Exception as e:
                logger.error(f"执行插件 {plugin.sector_id} 失败: {e}")
                results[plugin.sector_id] = {"error": str(e)}
        
        return results
    
    @classmethod
    async def run_sector(cls, sector_id: str) -> Dict:
        """
        运行指定板块的插件
        
        Args:
            sector_id: 板块ID
        """
        plugin = cls.get(sector_id)
        if not plugin:
            raise ValueError(f"未找到插件: {sector_id}")
        
        return await plugin.run_full_cycle()


# 便捷函数
def get_plugin(sector_id: str) -> Optional[SectorPlugin]:
    """获取插件"""
    return PluginRegistry.get(sector_id)


def get_enabled_plugins() -> List[SectorPlugin]:
    """获取所有启用的插件"""
    return PluginRegistry.get_enabled()
