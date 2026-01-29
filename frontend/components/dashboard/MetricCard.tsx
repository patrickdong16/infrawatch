"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  status?: "good" | "warning" | "danger" | "neutral";
  description?: string;
  trend?: {
    value: number;
    direction: "up" | "down" | "stable";
  };
}

const STATUS_STYLES = {
  good: {
    border: "border-green-200",
    bg: "bg-green-50",
    text: "text-green-700",
    glow: "shadow-green-100",
  },
  warning: {
    border: "border-amber-200",
    bg: "bg-amber-50",
    text: "text-amber-700",
    glow: "shadow-amber-100",
  },
  danger: {
    border: "border-red-200",
    bg: "bg-red-50",
    text: "text-red-700",
    glow: "shadow-red-100",
  },
  neutral: {
    border: "border-gray-200",
    bg: "bg-gray-50",
    text: "text-gray-700",
    glow: "shadow-gray-100",
  },
};

export function MetricCard({
  title,
  value,
  unit,
  status = "neutral",
  description,
  trend,
}: MetricCardProps) {
  const styles = STATUS_STYLES[status];

  return (
    <div
      className={cn(
        "bg-white rounded-xl border p-4 transition-all duration-200 hover:shadow-md",
        styles.border
      )}
    >
      <div className="flex items-start justify-between">
        <span className="text-sm text-gray-500">{title}</span>
        {trend && (
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
    </div>
  );
}
