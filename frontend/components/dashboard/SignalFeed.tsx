"use client";

import Link from "next/link";
import { Bell, ChevronRight } from "lucide-react";
import { cn, formatRelativeTime, getSeverityBg, getSeverityColor } from "@/lib/utils";

interface Signal {
  id: number;
  triggered_at: string;
  signal_type: string;
  description: string;
  severity: "high" | "medium" | "low";
  is_read: boolean;
}

const MOCK_SIGNALS: Signal[] = [
  {
    id: 1,
    triggered_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    signal_type: "price_move",
    description: "DeepSeek V3 输入价格下调 20%",
    severity: "high",
    is_read: false,
  },
  {
    id: 2,
    triggered_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    signal_type: "supply_chain_alert",
    description: "HBM3e价格连续3月上涨，触发成本预警",
    severity: "high",
    is_read: false,
  },
  {
    id: 3,
    triggered_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    signal_type: "adoption_inflection",
    description: "Microsoft Copilot 万席客户数环比 +45%",
    severity: "medium",
    is_read: true,
  },
];

const SEVERITY_ICONS = {
  high: "🔴",
  medium: "🟡",
  low: "🟢",
};

const SIGNAL_TYPE_LABELS: Record<string, string> = {
  price_move: "价格变动",
  adoption_inflection: "采用拐点",
  coverage_threshold: "覆盖率阈值",
  supply_demand_shift: "供需变化",
  supply_chain_alert: "供应链预警",
};

export function SignalFeed() {
  const signals = MOCK_SIGNALS;
  const unreadCount = signals.filter((s) => !s.is_read).length;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">最新信号</h2>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">
              {unreadCount} 未读
            </span>
          )}
        </div>
        <Link
          href="/signals"
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
        >
          查看全部
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="space-y-3">
        {signals.map((signal) => (
          <div
            key={signal.id}
            className={cn(
              "border-l-4 rounded-r-lg p-3 transition-colors",
              getSeverityBg(signal.severity),
              !signal.is_read && "bg-opacity-70"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <span>{SEVERITY_ICONS[signal.severity]}</span>
                <span className="text-xs text-gray-500">
                  {formatRelativeTime(signal.triggered_at)}
                </span>
                <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded">
                  {SIGNAL_TYPE_LABELS[signal.signal_type] || signal.signal_type}
                </span>
              </div>
              {!signal.is_read && (
                <span className="w-2 h-2 bg-blue-500 rounded-full" />
              )}
            </div>
            <p className="mt-1 text-sm text-gray-700">{signal.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
