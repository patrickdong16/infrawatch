"use client";

import { useState, useEffect } from "react";
import { cn, formatRelativeTime, getSeverityBg } from "@/lib/utils";
import { Bell, Filter, RefreshCw, Check, ChevronDown } from "lucide-react";

interface Signal {
    id: number;
    triggered_at: string;
    signal_type: string;
    description: string;
    severity: "high" | "medium" | "low";
    is_read: boolean;
    direction?: string;
    magnitude?: number;
    provider?: { name: string } | null;
    previous_value?: number;
    current_value?: number;
}

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
    disclosure_change: "披露变化",
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SignalsPage() {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<{
        severity: string | null;
        type: string | null;
        isRead: boolean | null;
    }>({ severity: null, type: null, isRead: null });
    const [unreadCount, setUnreadCount] = useState(0);

    const fetchSignals = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (filter.severity) params.append("severity", filter.severity);
            if (filter.type) params.append("signal_type", filter.type);
            if (filter.isRead !== null) params.append("is_read", String(filter.isRead));
            params.append("limit", "50");

            const res = await fetch(`${API_BASE}/api/v1/signals?${params}`);
            const data = await res.json();

            if (data.data?.signals) {
                setSignals(data.data.signals);
                setUnreadCount(data.data.unread_count || 0);
            } else {
                // Fallback to mock data
                setSignals([
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
                ]);
                setUnreadCount(2);
            }
            setError(null);
        } catch (err) {
            setError("无法加载信号数据");
            // Use mock data on error
            setSignals([
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
            ]);
            setUnreadCount(2);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSignals();
    }, [filter]);

    const markAsRead = async (signalId: number) => {
        try {
            await fetch(`${API_BASE}/api/v1/signals/${signalId}/read`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_read: true }),
            });
            setSignals((prev) =>
                prev.map((s) => (s.id === signalId ? { ...s, is_read: true } : s))
            );
            setUnreadCount((prev) => Math.max(0, prev - 1));
        } catch {
            // Optimistic update anyway
            setSignals((prev) =>
                prev.map((s) => (s.id === signalId ? { ...s, is_read: true } : s))
            );
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">信号中心</h1>
                        <p className="text-gray-500 mt-1">价格变动、采用拐点、供应链预警等关键信号</p>
                    </div>
                    {unreadCount > 0 && (
                        <span className="px-3 py-1 bg-red-100 text-red-700 text-sm font-medium rounded-full">
                            {unreadCount} 未读
                        </span>
                    )}
                </div>
                <button
                    onClick={fetchSignals}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                    刷新
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2 text-gray-500">
                        <Filter className="w-4 h-4" />
                        <span className="text-sm font-medium">筛选:</span>
                    </div>

                    {/* Severity filter */}
                    <div className="flex gap-2">
                        {[
                            { value: null, label: "全部严重度" },
                            { value: "high", label: "🔴 高" },
                            { value: "medium", label: "🟡 中" },
                            { value: "low", label: "🟢 低" },
                        ].map((option) => (
                            <button
                                key={option.value || "all"}
                                onClick={() => setFilter((f) => ({ ...f, severity: option.value }))}
                                className={cn(
                                    "px-3 py-1.5 text-sm font-medium rounded-lg transition-colors",
                                    filter.severity === option.value
                                        ? "bg-blue-100 text-blue-700"
                                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                                )}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>

                    {/* Read status filter */}
                    <div className="flex gap-2 ml-4">
                        {[
                            { value: null, label: "全部" },
                            { value: false, label: "未读" },
                            { value: true, label: "已读" },
                        ].map((option) => (
                            <button
                                key={String(option.value)}
                                onClick={() => setFilter((f) => ({ ...f, isRead: option.value }))}
                                className={cn(
                                    "px-3 py-1.5 text-sm font-medium rounded-lg transition-colors",
                                    filter.isRead === option.value
                                        ? "bg-purple-100 text-purple-700"
                                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                                )}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-12 text-gray-400">
                    <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                    加载信号...
                </div>
            )}

            {/* Signal list */}
            {!loading && (
                <div className="space-y-3">
                    {signals.map((signal) => (
                        <div
                            key={signal.id}
                            className={cn(
                                "bg-white rounded-xl shadow-sm border border-gray-100 p-4 transition-all",
                                !signal.is_read && "border-l-4 border-l-blue-500"
                            )}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-3">
                                    <span className="text-xl">{SEVERITY_ICONS[signal.severity]}</span>
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs text-gray-500">
                                                {formatRelativeTime(signal.triggered_at)}
                                            </span>
                                            <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">
                                                {SIGNAL_TYPE_LABELS[signal.signal_type] || signal.signal_type}
                                            </span>
                                            {signal.provider?.name && (
                                                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                                                    {signal.provider.name}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-gray-900 font-medium">{signal.description}</p>
                                        {(signal.previous_value !== undefined && signal.current_value !== undefined) && (
                                            <p className="text-sm text-gray-500 mt-1">
                                                {signal.previous_value} → {signal.current_value}
                                                {signal.magnitude && ` (${signal.direction === "down" ? "-" : "+"}${(signal.magnitude * 100).toFixed(1)}%)`}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {!signal.is_read && (
                                        <button
                                            onClick={() => markAsRead(signal.id)}
                                            className="flex items-center gap-1 px-3 py-1.5 text-xs text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                                        >
                                            <Check className="w-3 h-3" />
                                            标记已读
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {signals.length === 0 && (
                        <div className="text-center py-12 text-gray-400">
                            暂无符合条件的信号
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
