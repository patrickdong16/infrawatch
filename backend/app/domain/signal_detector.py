"""
Signal Detector - 信号检测模块

根据 REQUIREMENTS.md 规范检测和触发信号:
- price_move: 价格显著变动
- coverage_threshold: M01 覆盖率跨越阈值
- supply_demand_shift: 供需格局变化
- adoption_inflection: 采用率拐点
- disclosure_change: 披露口径变化
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """信号类型"""
    PRICE_MOVE = "price_move"
    COVERAGE_THRESHOLD = "coverage_threshold"
    SUPPLY_DEMAND_SHIFT = "supply_demand_shift"
    ADOPTION_INFLECTION = "adoption_inflection"
    DISCLOSURE_CHANGE = "disclosure_change"
    SUPPLY_CHAIN_ALERT = "supply_chain_alert"


class Severity(str, Enum):
    """严重程度"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Signal:
    """信号数据"""
    signal_type: SignalType
    severity: Severity
    title: str
    description: str
    metric_id: str
    current_value: float
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    threshold: Optional[float] = None
    sector: Optional[str] = None
    provider: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_read: bool = False


class SignalDetector:
    """
    信号检测器
    
    阈值定义 (来自 CLAUDE.md):
    - price_move HIGH: 周环比 > 10%
    - price_move MEDIUM: 周环比 5-10%
    - adoption_inflection MEDIUM: 季度环比 > 20%
    - coverage_threshold HIGH: M01 跨越 0.3/0.7/1.0
    """
    
    # 阈值配置
    THRESHOLDS = {
        "price_move": {
            "high": 0.10,      # 10% 周环比
            "medium": 0.05,    # 5% 周环比
        },
        "adoption_inflection": {
            "medium": 0.20,    # 20% 季度环比
        },
        "supply_demand_shift": {
            "spot_discount_change": 0.10,  # 10pp
        },
        "m01_thresholds": [0.3, 0.7, 1.0],
    }
    
    def __init__(self):
        self.signals: List[Signal] = []
    
    def detect_price_signal(
        self,
        metric_id: str,
        current_price: float,
        previous_price: float,
        sector: str = "B",
        provider: str = None,
    ) -> Optional[Signal]:
        """
        检测价格变动信号
        
        Args:
            metric_id: 指标ID
            current_price: 当前价格
            previous_price: 上期价格
            sector: 板块 (B/C/E)
            provider: 供应商
        """
        if previous_price == 0:
            return None
        
        change_percent = (current_price - previous_price) / previous_price
        abs_change = abs(change_percent)
        
        # 判断严重程度
        if abs_change >= self.THRESHOLDS["price_move"]["high"]:
            severity = Severity.HIGH
        elif abs_change >= self.THRESHOLDS["price_move"]["medium"]:
            severity = Severity.MEDIUM
        else:
            return None  # 变动不显著，不触发信号
        
        direction = "上涨" if change_percent > 0 else "下跌"
        
        signal = Signal(
            signal_type=SignalType.PRICE_MOVE,
            severity=severity,
            title=f"{sector}板块价格{direction}",
            description=f"{provider or metric_id} 价格{direction} {abs(change_percent)*100:.1f}%",
            metric_id=metric_id,
            current_value=current_price,
            previous_value=previous_price,
            change_percent=change_percent * 100,
            sector=sector,
            provider=provider,
        )
        
        self.signals.append(signal)
        logger.info(f"检测到价格信号: {signal.title} ({severity.value})")
        return signal
    
    def detect_coverage_threshold(
        self,
        m01_low: float,
        m01_high: float,
        previous_m01_low: Optional[float] = None,
        previous_m01_high: Optional[float] = None,
    ) -> Optional[Signal]:
        """
        检测 M01 覆盖率阈值跨越
        
        阈值: 0.3 (临界), 0.7 (健康), 1.0 (自养)
        """
        thresholds = self.THRESHOLDS["m01_thresholds"]
        
        for threshold in thresholds:
            # 检查是否向上跨越
            if previous_m01_low is not None:
                if previous_m01_low < threshold <= m01_low:
                    signal = Signal(
                        signal_type=SignalType.COVERAGE_THRESHOLD,
                        severity=Severity.HIGH,
                        title=f"M01 向上跨越 {threshold}",
                        description=f"M01 覆盖率从 {previous_m01_low:.2f} 上升至 {m01_low:.2f}，跨越 {threshold} 阈值",
                        metric_id="m01_coverage",
                        current_value=m01_low,
                        previous_value=previous_m01_low,
                        threshold=threshold,
                        metadata={"direction": "up", "m01_high": m01_high},
                    )
                    self.signals.append(signal)
                    logger.info(f"检测到覆盖率信号: {signal.title}")
                    return signal
                
                # 检查是否向下跨越
                if previous_m01_low >= threshold > m01_low:
                    signal = Signal(
                        signal_type=SignalType.COVERAGE_THRESHOLD,
                        severity=Severity.HIGH,
                        title=f"M01 向下跨越 {threshold}",
                        description=f"M01 覆盖率从 {previous_m01_low:.2f} 下降至 {m01_low:.2f}，跌破 {threshold} 阈值",
                        metric_id="m01_coverage",
                        current_value=m01_low,
                        previous_value=previous_m01_low,
                        threshold=threshold,
                        metadata={"direction": "down", "m01_high": m01_high},
                    )
                    self.signals.append(signal)
                    logger.info(f"检测到覆盖率信号: {signal.title}")
                    return signal
        
        return None
    
    def detect_supply_demand_shift(
        self,
        current_spot_discount: float,
        previous_spot_discount: float,
    ) -> Optional[Signal]:
        """
        检测供需格局变化
        
        触发条件: C_spot_discount 变化 > 10pp
        """
        change = abs(current_spot_discount - previous_spot_discount)
        threshold = self.THRESHOLDS["supply_demand_shift"]["spot_discount_change"]
        
        if change < threshold:
            return None
        
        direction = "扩大" if current_spot_discount > previous_spot_discount else "收窄"
        
        signal = Signal(
            signal_type=SignalType.SUPPLY_DEMAND_SHIFT,
            severity=Severity.MEDIUM,
            title=f"GPU Spot 折扣{direction}",
            description=f"Spot 折扣从 {previous_spot_discount*100:.1f}% 变化至 {current_spot_discount*100:.1f}%",
            metric_id="c_spot_discount",
            current_value=current_spot_discount,
            previous_value=previous_spot_discount,
            change_percent=change * 100,
            sector="C",
        )
        
        self.signals.append(signal)
        logger.info(f"检测到供需信号: {signal.title}")
        return signal
    
    def detect_adoption_inflection(
        self,
        metric_id: str,
        current_value: float,
        previous_value: float,
        metric_name: str = None,
    ) -> Optional[Signal]:
        """
        检测采用率拐点
        
        触发条件: 季度环比 > 20%
        """
        if previous_value == 0:
            return None
        
        change_percent = (current_value - previous_value) / previous_value
        
        if abs(change_percent) < self.THRESHOLDS["adoption_inflection"]["medium"]:
            return None
        
        direction = "加速" if change_percent > 0 else "放缓"
        
        signal = Signal(
            signal_type=SignalType.ADOPTION_INFLECTION,
            severity=Severity.MEDIUM,
            title=f"A板块采用{direction}",
            description=f"{metric_name or metric_id} 季度环比 {change_percent*100:+.1f}%",
            metric_id=metric_id,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent * 100,
            sector="A",
        )
        
        self.signals.append(signal)
        logger.info(f"检测到采用信号: {signal.title}")
        return signal
    
    def get_recent_signals(self, limit: int = 10) -> List[Signal]:
        """获取最近的信号"""
        return sorted(
            self.signals,
            key=lambda s: s.created_at,
            reverse=True
        )[:limit]
    
    def get_unread_signals(self) -> List[Signal]:
        """获取未读信号"""
        return [s for s in self.signals if not s.is_read]
    
    def mark_as_read(self, signal: Signal) -> None:
        """标记信号为已读"""
        signal.is_read = True
    
    def to_dict(self, signal: Signal) -> Dict[str, Any]:
        """转换信号为字典"""
        return {
            "signal_type": signal.signal_type.value,
            "severity": signal.severity.value,
            "title": signal.title,
            "description": signal.description,
            "metric_id": signal.metric_id,
            "current_value": signal.current_value,
            "previous_value": signal.previous_value,
            "change_percent": signal.change_percent,
            "threshold": signal.threshold,
            "sector": signal.sector,
            "provider": signal.provider,
            "created_at": signal.created_at.isoformat(),
            "is_read": signal.is_read,
        }


# 全局检测器实例
_detector: Optional[SignalDetector] = None


def get_detector() -> SignalDetector:
    """获取全局检测器实例"""
    global _detector
    if _detector is None:
        _detector = SignalDetector()
    return _detector


def detect_all_signals(prices: List[Dict], previous_prices: List[Dict] = None) -> List[Dict]:
    """
    批量检测价格信号
    
    便捷函数，可被 API 或 Celery 任务调用
    """
    detector = get_detector()
    
    if not previous_prices:
        return []
    
    # 创建价格查找表
    prev_lookup = {
        (p.get("provider"), p.get("sku_id")): p 
        for p in previous_prices
    }
    
    for current in prices:
        key = (current.get("provider"), current.get("sku_id"))
        previous = prev_lookup.get(key)
        
        if previous:
            curr_price = current.get("input_price") or current.get("hourly_rate") or 0
            prev_price = previous.get("input_price") or previous.get("hourly_rate") or 0
            
            if curr_price > 0 and prev_price > 0:
                sector = "C" if current.get("hourly_rate") else "B"
                detector.detect_price_signal(
                    metric_id=current.get("sku_id"),
                    current_price=curr_price,
                    previous_price=prev_price,
                    sector=sector,
                    provider=current.get("provider"),
                )
    
    return [detector.to_dict(s) for s in detector.get_recent_signals()]
