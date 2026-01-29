"""Stage determination engine - determines current infrastructure sustainability stage."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models import StageCode, Confidence


@dataclass
class StageMetrics:
    """Metrics required for stage determination."""
    m01_low: Optional[float] = None
    m01_high: Optional[float] = None
    b_qoq_deflation: Optional[float] = None  # Quarterly price deflation rate
    c_spot_discount: Optional[float] = None  # Spot discount rate
    c_rental_qoq: Optional[float] = None  # Rental price QoQ change
    a_growth_streak: int = 0  # Consecutive quarters of A-sector growth
    d3_margin_qoq: Optional[float] = None  # Cloud margin QoQ change
    e_supply_tightness: Optional[float] = None  # Supply chain tightness index


@dataclass
class StageResult:
    """Stage determination result."""
    stage: StageCode
    confidence: Confidence
    rationale: str
    trigger_conditions: dict[str, bool]
    transition_risks: dict[str, dict]
    metrics_snapshot: dict[str, Optional[float]]
    determined_at: datetime


class StageEngine:
    """Stage determination engine based on monitoring framework rules."""
    
    # Threshold configuration
    THRESHOLDS = {
        'M01_CRITICAL': 0.3,
        'M01_HEALTHY': 0.7,
        'M01_SUSTAINABLE': 1.0,
        'B_DEFLATION_SEVERE': 0.15,  # 15%
        'C_SPOT_EXCESS': 0.40,  # 40%
        'C_RENTAL_STABLE': 0.05,  # ±5%
        'D3_MARGIN_STABLE': 0.03,  # ±3pp
        'A_GROWTH_MIN_STREAK': 2,
        'E_SUPPLY_TIGHT': 0.80,  # Supply tightness threshold
    }
    
    # Stage definitions
    STAGE_INFO = {
        StageCode.S0: {
            'name': '不可持续',
            'description': '基建严重过剩，收入无法覆盖折旧，价格崩塌'
        },
        StageCode.S1: {
            'name': '临界过渡',
            'description': '收入快速增长但仍不足，供需紧平衡'
        },
        StageCode.S2: {
            'name': '早期自养',
            'description': 'M01接近1.0，价格稳定，企业采用加速'
        },
        StageCode.S3: {
            'name': '成熟工业化',
            'description': '完全自养，价格下降但毛利稳定'
        },
    }
    
    def determine(self, metrics: StageMetrics) -> StageResult:
        """Execute stage determination based on current metrics."""
        
        # Check conditions for each stage
        s0_conditions = self._check_s0_conditions(metrics)
        s3_conditions = self._check_s3_conditions(metrics)
        s2_conditions = self._check_s2_conditions(metrics)
        s1_conditions = self._check_s1_conditions(metrics)
        
        # Determine stage by priority
        if self._all_met(s0_conditions, min_count=3):
            stage = StageCode.S0
            confidence = Confidence.HIGH
            rationale = "M01过低 + 价格崩塌 + 产能过剩"
            trigger = s0_conditions
        
        elif self._all_met(s3_conditions, min_count=2):
            stage = StageCode.S3
            confidence = Confidence.HIGH
            rationale = "M01>1.0 + 云利润率稳定"
            trigger = s3_conditions
        
        elif self._all_met(s2_conditions, min_count=2):
            stage = StageCode.S2
            confidence = Confidence.HIGH
            rationale = "M01接近自养 + 供需平衡"
            trigger = s2_conditions
        
        elif self._any_met(s1_conditions):
            stage = StageCode.S1
            confidence = Confidence.HIGH if metrics.a_growth_streak >= 2 else Confidence.MEDIUM
            rationale = "M01过渡区间 或 企业采用持续增长"
            trigger = s1_conditions
        
        else:
            stage = StageCode.S1
            confidence = Confidence.LOW
            rationale = "指标信号混合，默认判定为过渡期"
            trigger = s1_conditions
        
        # Calculate transition risks
        transition_risks = self._calculate_transition_risks(stage, metrics)
        
        return StageResult(
            stage=stage,
            confidence=confidence,
            rationale=rationale,
            trigger_conditions=trigger,
            transition_risks=transition_risks,
            metrics_snapshot=self._to_snapshot(metrics),
            determined_at=datetime.utcnow()
        )
    
    def _check_s0_conditions(self, m: StageMetrics) -> dict[str, bool]:
        """Check S0 (Unsustainable) conditions."""
        conditions = {}
        
        if m.m01_high is not None:
            conditions['m01_too_low'] = m.m01_high < self.THRESHOLDS['M01_CRITICAL']
        
        if m.b_qoq_deflation is not None:
            conditions['price_collapse'] = m.b_qoq_deflation > self.THRESHOLDS['B_DEFLATION_SEVERE']
        
        if m.c_spot_discount is not None:
            conditions['capacity_excess'] = m.c_spot_discount > self.THRESHOLDS['C_SPOT_EXCESS']
        
        return conditions
    
    def _check_s3_conditions(self, m: StageMetrics) -> dict[str, bool]:
        """Check S3 (Mature Industrialization) conditions."""
        conditions = {}
        
        if m.m01_low is not None:
            conditions['m01_sustainable'] = m.m01_low > self.THRESHOLDS['M01_SUSTAINABLE']
        
        if m.d3_margin_qoq is not None:
            conditions['margin_stable'] = abs(m.d3_margin_qoq) < self.THRESHOLDS['D3_MARGIN_STABLE']
        
        return conditions
    
    def _check_s2_conditions(self, m: StageMetrics) -> dict[str, bool]:
        """Check S2 (Early Self-sustaining) conditions."""
        conditions = {}
        
        if m.m01_low is not None:
            conditions['m01_healthy'] = m.m01_low > self.THRESHOLDS['M01_HEALTHY']
        
        if m.c_rental_qoq is not None:
            conditions['rental_stable'] = abs(m.c_rental_qoq) < self.THRESHOLDS['C_RENTAL_STABLE']
        
        if m.e_supply_tightness is not None:
            conditions['supply_stable'] = m.e_supply_tightness < self.THRESHOLDS['E_SUPPLY_TIGHT']
        
        return conditions
    
    def _check_s1_conditions(self, m: StageMetrics) -> dict[str, bool]:
        """Check S1 (Critical Transition) conditions."""
        conditions = {}
        
        if m.m01_low is not None and m.m01_high is not None:
            conditions['m01_transition'] = (
                self.THRESHOLDS['M01_CRITICAL'] <= m.m01_high and
                m.m01_low <= self.THRESHOLDS['M01_HEALTHY']
            )
        
        conditions['adoption_growing'] = m.a_growth_streak >= self.THRESHOLDS['A_GROWTH_MIN_STREAK']
        
        return conditions
    
    def _all_met(self, conditions: dict[str, bool], min_count: int = 0) -> bool:
        """Check if all conditions are met (with minimum count)."""
        met = [v for v in conditions.values() if v is True]
        return len(met) >= min_count and all(conditions.values())
    
    def _any_met(self, conditions: dict[str, bool]) -> bool:
        """Check if any condition is met."""
        return any(conditions.values())
    
    def _calculate_transition_risks(
        self,
        current_stage: StageCode,
        m: StageMetrics
    ) -> dict[str, dict]:
        """Calculate transition risks to other stages."""
        risks = {}
        
        if current_stage == StageCode.S1:
            # S1 → S0 risk
            s0_conds = self._check_s0_conditions(m)
            met_count = sum(1 for v in s0_conds.values() if v)
            risks['to_S0'] = {
                'probability': 'high' if met_count >= 2 else 'low',
                'conditions_met': met_count,
                'conditions_total': 3,
                'details': s0_conds
            }
            
            # S1 → S2 opportunity
            s2_conds = self._check_s2_conditions(m)
            met_count = sum(1 for v in s2_conds.values() if v)
            m01_gap = max(0, self.THRESHOLDS['M01_HEALTHY'] - (m.m01_low or 0))
            risks['to_S2'] = {
                'probability': 'high' if met_count >= 2 else 'medium' if met_count >= 1 else 'low',
                'conditions_met': met_count,
                'conditions_total': 2,
                'details': s2_conds,
                'gap': {'m01_needed': round(m01_gap, 2)}
            }
        
        elif current_stage == StageCode.S2:
            # S2 → S3 opportunity
            s3_conds = self._check_s3_conditions(m)
            met_count = sum(1 for v in s3_conds.values() if v)
            m01_gap = max(0, self.THRESHOLDS['M01_SUSTAINABLE'] - (m.m01_low or 0))
            risks['to_S3'] = {
                'probability': 'high' if met_count >= 2 else 'medium',
                'conditions_met': met_count,
                'conditions_total': 2,
                'gap': {'m01_needed': round(m01_gap, 2)}
            }
            
            # S2 → S1 risk
            risks['to_S1'] = {
                'probability': 'low',
                'conditions_met': 0,
                'conditions_total': 2,
                'details': {}
            }
        
        return risks
    
    def _to_snapshot(self, m: StageMetrics) -> dict[str, Optional[float]]:
        """Convert metrics to snapshot dictionary."""
        return {
            'm01_low': m.m01_low,
            'm01_high': m.m01_high,
            'b_qoq_deflation': m.b_qoq_deflation,
            'c_spot_discount': m.c_spot_discount,
            'c_rental_qoq': m.c_rental_qoq,
            'a_growth_streak': float(m.a_growth_streak),
            'd3_margin_qoq': m.d3_margin_qoq,
            'e_supply_tightness': m.e_supply_tightness,
        }
    
    def get_stage_info(self, stage: StageCode) -> dict:
        """Get stage information."""
        return self.STAGE_INFO.get(stage, {})
