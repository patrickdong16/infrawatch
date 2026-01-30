"use client";

import { useState } from "react";
import useSWR from "swr";
import { TrendingUp, TrendingDown, DollarSign, Building2 } from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface CompanyData {
    ticker: string;
    name: string;
    focus: string;
    revenue: number;
    revenue_qoq: number | null;
    capex: number;
    capex_qoq: number | null;
}

interface GrowthData {
    quarter: string;
    revenue_qoq: number | null;
    capex_qoq: number | null;
}

function formatBillion(value: number): string {
    return `$${(value / 1e9).toFixed(1)}B`;
}

function GrowthBadge({ value }: { value: number | null }) {
    if (value === null) return <span className="text-gray-400">-</span>;
    const isPositive = value > 0;
    return (
        <span
            className={`inline-flex items-center gap-0.5 text-xs font-medium px-2 py-0.5 rounded-full ${isPositive ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                }`}
        >
            {isPositive ? (
                <TrendingUp className="w-3 h-3" />
            ) : (
                <TrendingDown className="w-3 h-3" />
            )}
            {value > 0 ? "+" : ""}
            {value.toFixed(1)}%
        </span>
    );
}

export function AIFinancialsCard() {
    const { data: metricsData } = useSWR(
        `${API_BASE}/api/v1/financials/ai-metrics`,
        fetcher,
        { refreshInterval: 300000 }
    );
    const { data: growthData } = useSWR(
        `${API_BASE}/api/v1/financials/growth-comparison`,
        fetcher,
        { refreshInterval: 300000 }
    );

    const companies: CompanyData[] = metricsData?.data?.companies || [];
    const summary = metricsData?.data?.summary;
    const growthSeries: GrowthData[] = growthData?.data?.series || [];

    // 只取最近 6 个季度
    const chartData = growthSeries.slice(-6).map((item) => ({
        quarter: item.quarter.slice(0, 7), // 2025-12
        收入增速: item.revenue_qoq,
        CapEx增速: item.capex_qoq,
    }));

    if (!companies.length) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="text-center text-gray-400">加载财务数据...</div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-gray-900">AI 巨头财务指标</h3>
                </div>
                {summary && (
                    <div className="text-xs text-gray-500">
                        CapEx/收入: <span className="font-medium text-amber-600">{summary.capex_to_revenue_ratio}%</span>
                    </div>
                )}
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-3">
                    <div className="text-xs text-blue-600 mb-1">总收入 (6家合计)</div>
                    <div className="text-xl font-bold text-blue-900">
                        ${summary?.total_revenue_b}B
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        季环比 <GrowthBadge value={summary?.avg_revenue_qoq} />
                    </div>
                </div>
                <div className="bg-amber-50 rounded-lg p-3">
                    <div className="text-xs text-amber-600 mb-1">总 CapEx (数据中心)</div>
                    <div className="text-xl font-bold text-amber-900">
                        ${summary?.total_capex_b}B
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        季环比 <GrowthBadge value={summary?.avg_capex_qoq} />
                    </div>
                </div>
            </div>

            {/* Growth Comparison Chart */}
            {chartData.length > 0 && (
                <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">
                        收入增速 vs CapEx增速 (QoQ)
                    </h4>
                    <ResponsiveContainer width="100%" height={180}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis
                                dataKey="quarter"
                                tick={{ fontSize: 10 }}
                                tickLine={false}
                            />
                            <YAxis
                                tick={{ fontSize: 10 }}
                                tickLine={false}
                                tickFormatter={(v) => `${v}%`}
                            />
                            <Tooltip
                                formatter={(value: number) => [`${value?.toFixed(1)}%`]}
                            />
                            <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                            <Line
                                type="monotone"
                                dataKey="收入增速"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                dot={{ fill: "#3b82f6", r: 3 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="CapEx增速"
                                stroke="#f59e0b"
                                strokeWidth={2}
                                dot={{ fill: "#f59e0b", r: 3 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Company List */}
            <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">各公司详情</h4>
                <div className="divide-y divide-gray-100">
                    {companies.slice(0, 4).map((company) => (
                        <div
                            key={company.ticker}
                            className="py-2 flex items-center justify-between"
                        >
                            <div>
                                <div className="font-medium text-gray-900 text-sm">
                                    {company.name}
                                </div>
                                <div className="text-xs text-gray-500">{company.focus}</div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-medium">
                                    {formatBillion(company.revenue)}
                                </div>
                                <div className="flex items-center gap-2 justify-end">
                                    <span className="text-xs text-gray-400">CapEx:</span>
                                    <GrowthBadge value={company.capex_qoq} />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
