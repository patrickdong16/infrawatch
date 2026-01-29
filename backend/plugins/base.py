"""
板块插件基类
定义插件接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from app.core.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """插件相关异常"""
    pass


class SectorPlugin(ABC):
    """
    板块插件基类
    
    每个板块(A/B/C/D/E)实现自己的插件，负责:
    1. 数据采集 (爬虫/API调用)
    2. 派生指标计算
    3. 信号检测
    """
    
    # 子类必须定义
    sector_id: str = ""
    
    def __init__(self):
        if not self.sector_id:
            raise PluginError(f"{self.__class__.__name__} 必须定义 sector_id")
        self._config: Optional[Dict[str, Any]] = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取板块配置 (懒加载)"""
        if self._config is None:
            self._config = ConfigLoader.load_sector(self.sector_id)
        return self._config
    
    @property
    def sector_name(self) -> str:
        """板块名称"""
        return self.config.get("sector", {}).get("name", self.sector_id)
    
    @property
    def providers(self) -> List[Dict[str, Any]]:
        """获取启用的供应商列表"""
        return ConfigLoader.get_providers_for_sector(self.sector_id)
    
    def is_enabled(self) -> bool:
        """检查板块是否启用"""
        return self.config.get("sector", {}).get("enabled", True)
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = None
        logger.info(f"已重新加载 {self.sector_id} 板块配置")
    
    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        采集数据
        
        Returns:
            采集到的数据记录列表，每条记录包含:
            - provider_id: 供应商ID
            - sku_id: SKU ID
            - value_data: 数据值 (JSONB)
            - source_url: 数据来源
            - recorded_at: 采集时间
        """
        pass
    
    @abstractmethod
    async def calculate_derived(self) -> List[Dict[str, Any]]:
        """
        计算派生指标
        
        Returns:
            派生指标列表，每条记录包含:
            - metric_id: 指标ID
            - value_data: 计算结果 (JSONB)
            - inputs: 输入数据引用
        """
        pass
    
    async def detect_signals(self) -> List[Dict[str, Any]]:
        """
        检测信号 (可选覆盖)
        
        默认使用通用信号检测器
        """
        return []
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """
        执行完整周期: 采集 -> 计算 -> 检测
        """
        result = {
            "sector_id": self.sector_id,
            "started_at": datetime.utcnow().isoformat(),
            "collected": [],
            "derived": [],
            "signals": [],
            "errors": []
        }
        
        try:
            # 1. 采集数据
            logger.info(f"[{self.sector_id}] 开始数据采集...")
            result["collected"] = await self.collect()
            logger.info(f"[{self.sector_id}] 采集完成: {len(result['collected'])} 条")
            
            # 2. 计算派生指标
            logger.info(f"[{self.sector_id}] 开始计算派生指标...")
            result["derived"] = await self.calculate_derived()
            logger.info(f"[{self.sector_id}] 计算完成: {len(result['derived'])} 条")
            
            # 3. 信号检测
            logger.info(f"[{self.sector_id}] 开始信号检测...")
            result["signals"] = await self.detect_signals()
            logger.info(f"[{self.sector_id}] 检测完成: {len(result['signals'])} 条")
            
        except Exception as e:
            logger.error(f"[{self.sector_id}] 执行失败: {e}")
            result["errors"].append(str(e))
        
        result["finished_at"] = datetime.utcnow().isoformat()
        return result


class SpiderMixin:
    """
    爬虫功能混入类
    提供通用的爬虫辅助方法
    """
    
    async def run_spider(self, spider_class: str, provider_config: Dict[str, Any]):
        """
        动态加载并运行爬虫
        
        Args:
            spider_class: 爬虫类路径，如 'plugins.sectors.sector_b.OpenAIPricingSpider'
            provider_config: 供应商配置
        """
        from importlib import import_module
        
        # 动态导入爬虫类
        module_path, class_name = spider_class.rsplit('.', 1)
        module = import_module(module_path)
        spider_cls = getattr(module, class_name)
        
        # 实例化并运行
        spider = spider_cls(provider_config)
        return await spider.run()
