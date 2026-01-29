import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(price);
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "刚刚";
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;
  return formatDate(date);
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "high":
      return "text-red-500";
    case "medium":
      return "text-amber-500";
    case "low":
      return "text-green-500";
    default:
      return "text-gray-500";
  }
}

export function getSeverityBg(severity: string): string {
  switch (severity) {
    case "high":
      return "bg-red-50 border-red-200";
    case "medium":
      return "bg-amber-50 border-amber-200";
    case "low":
      return "bg-green-50 border-green-200";
    default:
      return "bg-gray-50 border-gray-200";
  }
}

export function getStageColor(stage: string): string {
  switch (stage) {
    case "S0":
      return "#ef4444";
    case "S1":
      return "#f59e0b";
    case "S2":
      return "#84cc16";
    case "S3":
      return "#22c55e";
    default:
      return "#6b7280";
  }
}

export function getStagePosition(stage: string): number {
  switch (stage) {
    case "S0":
      return 12.5;
    case "S1":
      return 37.5;
    case "S2":
      return 62.5;
    case "S3":
      return 87.5;
    default:
      return 50;
  }
}
