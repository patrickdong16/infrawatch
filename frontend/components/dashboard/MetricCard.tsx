"use client";

import { TrendingUp, TrendingDown, Minus, HelpCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface TrendData {
  value: number;
  direction: "up" | "down" | "stable";
  label?: string;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  status?: "good" | "warning" | "danger" | "neutral";
  description?: string;
  trend?: TrendData;
  // 趋势数据
  weekOverWeek?: number;
  monthOverMonth?: number;
  yearOverYear?: number;
  // 指标定义
  definition?: string;
  usage?: string;
}

// 预定义的指标说明
const METRIC_DEFINITIONS: Record<string, { definition: string; usage: string }> = {
  "M01 覆盖率": {
    definition: "M01 (Inference Coverage Ratio) 衡量企业 AI 推理成本占总运营成本的比例，是判断行业周期阶段的核心指标。",
    usage: "• < 0.24: S0 萌芽期\n• 0.24-0.36: S1 过渡期\n• 0.36-0.48: S2 成熟期\n• > 0.48: S3 巅峰期"
  },
  "推理价格指数": {
    definition: "B板块主要模型 API 的加权平均推理价格（每百万 tokens），反映模型服务的整体定价水平。",
    usage: "价格下降 → 利好企业采用\n价格上升 → 供需紧张信号"
  },
  "H100 小时价": {
    definition: "NVIDIA H100 GPU 云租赁的平均小时价格，反映高端算力供需状况。",
    usage: "价格下降 → 算力供应充足\n价格上升 → 算力需求旺盛"
  },
  "B板块价格指数": {
    definition: "B板块（模型 API）的综合价格指数，包含主流 LLM 提供商的加权平均价格。",
    usage: "跟踪模型服务商定价策略变化，判断市场竞争态势"
  },
  "C板块价格指数": {
    definition: "C板块（GPU 租赁）的综合价格指数，反映云端算力的整体成本。",
    usage: "跟踪算力成本变化，评估基础设施投资时机"
  },
  "供应链紧张度": {
    definition: "E板块供应链紧张程度指数，综合 GPU 交期、产能利用率等因素。",
    usage: "• < 0.6: 供应充足\n• 0.6-0.8: 供需平衡\n• > 0.8: 供应紧张"
  },
};

const STATUS_STYLES = {
  good: {
    border: "border-green-200",
    bg: "bg-green-50",
    text: "text-green-700",
  },
  warning: {
    border: "border-amber-200",
    bg: "bg-amber-50",
    text: "text-amber-700",
  },
  danger: {
    border: "border-red-200",
    bg: "bg-red-50",
    text: "text-red-700",
  },
  neutral: {
    border: "border-gray-200",
    bg: "bg-gray-50",
    text: "text-gray-700",
  },
};

function TrendBadge({ value, label }: { value: number; label: string }) {
  const isPositive = value > 0;
  const isNegative = value < 0;

  return (
    <div
      className={cn(
        "flex items-center gap-0.5 text-xs font-medium px-1.5 py-0.5 rounded",
        isNegative ? "text-green-600 bg-green-50" :
          isPositive ? "text-red-600 bg-red-50" :
            "text-gray-500 bg-gray-50"
      )}
    >
      {isNegative ? (
        <TrendingDown className="w-3 h-3" />
      ) : isPositive ? (
        <TrendingUp className="w-3 h-3" />
      ) : (
        <Minus className="w-3 h-3" />
      )}
      <span>{value > 0 ? "+" : ""}{value.toFixed(1)}%</span>
      <span className="text-gray-400 ml-0.5">{label}</span>
    </div>
  );
}

export function MetricCard({
  title,
  value,
  unit,
  status = "neutral",
  description,
  trend,
  weekOverWeek,
  monthOverMonth,
  yearOverYear,
  definition,
  usage,
}: MetricCardProps) {
  const styles = STATUS_STYLES[status];
  const [showHelp, setShowHelp] = useState(false);

  const hasTrends = weekOverWeek !== undefined || monthOverMonth !== undefined || yearOverYear !== undefined;

  // 获取预定义说明或使用传入的
  const metricDef = METRIC_DEFINITIONS[title];
  const finalDefinition = definition || metricDef?.definition;
  const finalUsage = usage || metricDef?.usage;
  const hasHelp = finalDefinition || finalUsage;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border p-4 transition-all duration-200 hover:shadow-md relative",
        styles.border
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-gray-500">{title}</span>
          {hasHelp && (
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="text-gray-400 hover:text-blue-500 transition-colors"
              title="查看说明"
            >
              <HelpCircle className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        {trend && !hasTrends && (
          <div
            className={cn(
              "flex items-center gap-1 text-xs font-medium",
              trend.direction === "up" && trend.value > 0
                ? "text-green-600"
                : trend.direction === "down"
                  ? "text-red-600"
                  : "text-gray-500"
            )}
          >
            {trend.direction === "up" ? (
              <TrendingUp className="w-3 h-3" />
            ) : trend.direction === "down" ? (
              <TrendingDown className="w-3 h-3" />
            ) : (
              <Minus className="w-3 h-3" />
            )}
            <span>
              {trend.value > 0 ? "+" : ""}
              {trend.value}%
            </span>
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-1">
        <span className={cn("text-2xl font-bold", styles.text)}>{value}</span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>

      {description && (
        <p className="mt-1 text-xs text-gray-500">{description}</p>
      )}

      {/* 趋势标签 */}
      {hasTrends && (
        <div className="mt-3 flex flex-wrap gap-2">
          {weekOverWeek !== undefined && (
            <TrendBadge value={weekOverWeek} label="周" />
          )}
          {monthOverMonth !== undefined && (
            <TrendBadge value={monthOverMonth} label="月" />
          )}
          {yearOverYear !== undefined && (
            <TrendBadge value={yearOverYear} label="年" />
          )}
        </div>
      )}

      {/* 帮助弹出层 */}
      {showHelp && hasHelp && (
        <div className="absolute top-full left-0 right-0 mt-2 p-3 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <div className="flex items-start justify-between mb-2">
            <span className="text-sm font-medium text-gray-900">{title}</span>
            <button
              onClick={() => setShowHelp(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          {finalDefinition && (
            <div className="mb-2">
              <span className="text-xs font-medium text-gray-500">定义</span>
              <p className="text-xs text-gray-700 mt-0.5">{finalDefinition}</p>
            </div>
          )}
          {finalUsage && (
            <div>
              <span className="text-xs font-medium text-gray-500">使用说明</span>
              <p className="text-xs text-gray-700 mt-0.5 whitespace-pre-line">{finalUsage}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
