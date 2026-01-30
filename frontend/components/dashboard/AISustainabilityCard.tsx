"use client";

import useSWR from "swr";
import { TrendingUp, TrendingDown, DollarSign, Activity, Cloud, Minus } from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    BarChart,
    Bar,
    Cell,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fetcher = async (url: string) => {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch");
    return res.json();
};

interface SustainabilityData {
    capital_intensity: {
        current: number;
        qoq_change: number;
        trend: "up" | "down";
        description: string;
    };
    cloud_revenue: {
        total_b: number;
        qoq_growth: number;
        companies: Array<{
            company: string;
            segment: string;
            revenue_b: number;
            yoy_growth: number;
            qoq_growth: number;
            quarter: string;
        }>;
    };
    growth_comparison: {
        cloud_growth: number;
        capex_growth: number;
        spread: number;
        spread_trend: "positive" | "negative";
        series: Array<{
            quarter: string;
            cloud_growth: number;
            capex_growth: number | null;
        }>;
    };
}

// 颜色配置
const CLOUD_COLORS: Record<string, string> = {
    "Azure": "#0078D4",
    "AWS": "#FF9900",
    "Google Cloud": "#4285F4",
};

export function AISustainabilityCard() {
    const { data, error, isLoading } = useSWR<{ success: boolean; data: SustainabilityData }>(
        `${API_BASE}/api/v1/financials/sustainability`,
        fetcher,
        { refreshInterval: 120000 }
    );

    if (isLoading) {
        return (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-gray-200 rounded w-1/3" />
                    <div className="grid grid-cols-3 gap-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-24 bg-gray-100 rounded-xl" />
                        ))}
                    </div>
                    <div className="h-48 bg-gray-100 rounded-xl" />
                </div>
            </div>
        );
    }

    if (error || !data?.success) {
        return (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="text-red-500">加载可持续性数据失败</p>
            </div>
        );
    }

    const { capital_intensity, cloud_revenue, growth_comparison } = data.data;

    // 增速差趋势颜色
    const spreadColor = growth_comparison.spread >= 0 ? "text-green-600" : "text-amber-600";
    const spreadBgColor = growth_comparison.spread >= 0 ? "bg-green-50" : "bg-amber-50";
    const spreadIcon = growth_comparison.spread >= 0 ? (
        <TrendingUp className="w-4 h-4" />
    ) : (
        <TrendingDown className="w-4 h-4" />
    );

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-indigo-50 to-purple-50">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-indigo-600" />
                    AI 可持续性评分
                </h3>
                <p className="text-sm text-gray-500 mt-1">Cloud业务收入 vs AI基础设施投资</p>
            </div>

            <div className="p-6 space-y-6">
                {/* 三个核心指标 */}
                <div className="grid grid-cols-3 gap-4">
                    {/* 资本密集度 */}
                    <div className="bg-gray-50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
                            <DollarSign className="w-4 h-4" />
                            资本密集度
                        </div>
                        <div className="text-2xl font-bold text-gray-900">
                            {capital_intensity.current}%
                        </div>
                        <div className={`text-sm flex items-center gap-1 mt-1 ${capital_intensity.qoq_change > 0 ? "text-amber-600" : "text-green-600"
                            }`}>
                            {capital_intensity.qoq_change > 0 ? (
                                <TrendingUp className="w-3 h-3" />
                            ) : (
                                <TrendingDown className="w-3 h-3" />
                            )}
                            {capital_intensity.qoq_change > 0 ? "+" : ""}
                            {capital_intensity.qoq_change}pp
                        </div>
                    </div>

                    {/* Cloud 总收入 */}
                    <div className="bg-blue-50 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-blue-600 text-sm mb-2">
                            <Cloud className="w-4 h-4" />
                            Cloud 总收入
                        </div>
                        <div className="text-2xl font-bold text-gray-900">
                            ${cloud_revenue.total_b}B
                        </div>
                        <div className="text-sm text-green-600 flex items-center gap-1 mt-1">
                            <TrendingUp className="w-3 h-3" />
                            +{cloud_revenue.qoq_growth}% QoQ
                        </div>
                    </div>

                    {/* 增速差 */}
                    <div className={`${spreadBgColor} rounded-xl p-4`}>
                        <div className={`flex items-center gap-2 ${spreadColor} text-sm mb-2`}>
                            {spreadIcon}
                            增速差
                        </div>
                        <div className="text-2xl font-bold text-gray-900">
                            {growth_comparison.spread > 0 ? "+" : ""}
                            {growth_comparison.spread}pp
                        </div>
                        <div className={`text-sm ${spreadColor} mt-1`}>
                            {growth_comparison.spread >= 0 ? "Cloud > CapEx" : "CapEx > Cloud"}
                        </div>
                    </div>
                </div>

                {/* 增速对比图 */}
                <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">增速对比趋势</h4>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                                data={[
                                    { quarter: "Q1", cloud: 6.2, capex: 15.0 },
                                    { quarter: "Q2", cloud: 5.8, capex: 18.5 },
                                    { quarter: "Q3", cloud: 5.5, capex: 22.0 },
                                    { quarter: "Q4", cloud: 6.1, capex: 20.1 },
                                ]}
                                margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                <XAxis
                                    dataKey="quarter"
                                    fontSize={12}
                                    tickLine={false}
                                />
                                <YAxis
                                    fontSize={12}
                                    tickLine={false}
                                    tickFormatter={(v) => `${v}%`}
                                />
                                <Tooltip
                                    formatter={(value: number) => [`${value}%`, ""]}
                                    contentStyle={{ fontSize: 12 }}
                                />
                                <Legend
                                    wrapperStyle={{ fontSize: 12 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="cloud"
                                    name="Cloud收入增速"
                                    stroke="#4285F4"
                                    strokeWidth={2}
                                    dot={{ fill: "#4285F4", r: 4 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="capex"
                                    name="CapEx增速"
                                    stroke="#FF6B6B"
                                    strokeWidth={2}
                                    strokeDasharray="5 5"
                                    dot={{ fill: "#FF6B6B", r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Cloud 收入明细 */}
                <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Cloud 业务收入明细</h4>
                    <div className="space-y-3">
                        {cloud_revenue.companies.map((company) => {
                            const maxRevenue = Math.max(...cloud_revenue.companies.map(c => c.revenue_b));
                            const barWidth = (company.revenue_b / maxRevenue) * 100;
                            const color = CLOUD_COLORS[company.segment] || "#6B7280";

                            return (
                                <div key={company.segment} className="flex items-center gap-3">
                                    <div className="w-24 text-sm font-medium text-gray-700 truncate">
                                        {company.segment}
                                    </div>
                                    <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full rounded-full transition-all duration-500"
                                            style={{
                                                width: `${barWidth}%`,
                                                backgroundColor: color,
                                            }}
                                        />
                                    </div>
                                    <div className="w-20 text-right">
                                        <span className="text-sm font-semibold text-gray-900">
                                            ${company.revenue_b}B
                                        </span>
                                    </div>
                                    <div className="w-16 text-right">
                                        <span className="text-xs text-green-600 font-medium">
                                            +{Math.round(company.yoy_growth * 100)}%
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
