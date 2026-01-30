'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Scale, DollarSign, Server, AlertCircle, CheckCircle, HelpCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface QuarterlyData {
    quarter: string;
    revenue_b: number;
    revenue_growth: number;
    depreciation_b: number;
    depreciation_growth: number;
    net_difference: number;
    is_sustainable: boolean;
}

interface GrowthData {
    title: string;
    definitions: {
        revenue: string;
        depreciation: string;
        revenue_growth: string;
        depreciation_growth: string;
        net_difference: string;
    };
    summary: {
        latest_quarter: string;
        latest_revenue_b: number;
        latest_depreciation_b: number;
        latest_revenue_growth: number;
        latest_depreciation_growth: number;
        latest_net_difference: number;
        avg_net_4q: number;
        trend: string;
        trend_label: string;
    };
    quarterly_data: QuarterlyData[];
}

export default function ROIComparisonCard() {
    const [data, setData] = useState<GrowthData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showDefinitions, setShowDefinitions] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/v1/financials/growth-comparison`);
                const json = await res.json();
                if (json.success) {
                    setData(json.data);
                }
            } catch (e) {
                setError(e instanceof Error ? e.message : '获取数据失败');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="animate-pulse h-64 bg-white/50 rounded"></div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="bg-red-50 rounded-xl shadow-sm border border-red-100 p-6">
                <p className="text-red-600">{error || '数据加载失败'}</p>
            </div>
        );
    }

    const { summary, quarterly_data, definitions } = data;

    // 获取上一季度用于比较说明
    const prevQuarter = quarterly_data.length >= 2 ? quarterly_data[quarterly_data.length - 2].quarter : '';

    // 趋势配置
    const trendConfigs: Record<string, { icon: typeof CheckCircle; color: string; bg: string }> = {
        strong_growth: { icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50' },
        sustainable: { icon: CheckCircle, color: 'text-blue-600', bg: 'bg-blue-50' },
        attention: { icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-50' },
        risk: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50' },
    };
    const trendConfig = trendConfigs[summary.trend] || trendConfigs.attention;
    const TrendIcon = trendConfig.icon;

    // 为图表准备数据
    const chartData = quarterly_data.map(q => ({
        quarter: q.quarter.replace('20', "'"),
        revenue: q.revenue_b,
        depreciation: q.depreciation_b,
        revenueGrowth: q.revenue_growth,
        depreciationGrowth: q.depreciation_growth,
    }));

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            {/* 标题行 */}
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                            <Scale className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">挣钱速度 vs 花钱速度</h3>
                            <p className="text-xs text-gray-500">OpenAI + Anthropic 季度数据</p>
                        </div>
                        <button
                            onClick={() => setShowDefinitions(!showDefinitions)}
                            className="ml-2 text-gray-400 hover:text-indigo-600 transition-colors"
                            title="查看指标定义"
                        >
                            <HelpCircle className="w-4 h-4" />
                        </button>
                    </div>
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${trendConfig.bg}`}>
                        <TrendIcon className={`w-4 h-4 ${trendConfig.color}`} />
                        <span className={`text-sm font-medium ${trendConfig.color}`}>
                            {summary.trend_label}
                        </span>
                    </div>
                </div>
            </div>

            {/* 定义说明 (可折叠) */}
            {showDefinitions && (
                <div className="px-6 py-4 bg-indigo-50/50 border-b border-indigo-100 text-sm space-y-2">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <span className="font-medium text-indigo-700">📈 收入增速</span>
                            <p className="text-gray-600 text-xs mt-1">{definitions.revenue_growth}</p>
                        </div>
                        <div>
                            <span className="font-medium text-indigo-700">📉 成本增速</span>
                            <p className="text-gray-600 text-xs mt-1">{definitions.depreciation_growth}</p>
                        </div>
                    </div>
                    <p className="text-xs text-gray-500 pt-2 border-t border-indigo-100">
                        💡 净差值 = 收入增速 - 成本增速，正值表示挣钱比花钱快
                    </p>
                </div>
            )}

            <div className="p-6">
                {/* 核心对比：两列并排 */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                    {/* 左侧: 收入端 */}
                    <div className="rounded-xl p-5 bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-100">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                                    <DollarSign className="w-4 h-4 text-white" />
                                </div>
                                <span className="font-semibold text-gray-800">收入端</span>
                            </div>
                            {summary.latest_revenue_growth >= 0 ? (
                                <ArrowUpRight className="w-5 h-5 text-emerald-500" />
                            ) : (
                                <ArrowDownRight className="w-5 h-5 text-red-500" />
                            )}
                        </div>

                        {/* 绝对值 */}
                        <div className="mb-3">
                            <div className="text-3xl font-bold text-gray-900">
                                ${summary.latest_revenue_b}B
                            </div>
                            <div className="text-sm text-gray-500">
                                {summary.latest_quarter} 推理收入
                            </div>
                        </div>

                        {/* 趋势值 - 明确标注比较基准 */}
                        <div className="p-3 bg-white/60 rounded-lg">
                            <div className="flex items-baseline justify-between">
                                <div>
                                    <span className={`text-2xl font-bold ${summary.latest_revenue_growth >= 0 ? 'text-emerald-600' : 'text-red-600'
                                        }`}>
                                        {summary.latest_revenue_growth > 0 ? '+' : ''}{summary.latest_revenue_growth}%
                                    </span>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-gray-500">环比增速</div>
                                    <div className="text-xs text-gray-400">vs {prevQuarter}</div>
                                </div>
                            </div>
                        </div>

                        {/* 面积图 */}
                        <div className="h-28 mt-4 -mx-2">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                                    <defs>
                                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                                    <XAxis
                                        dataKey="quarter"
                                        tick={{ fontSize: 10, fill: '#6b7280' }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <YAxis hide domain={['auto', 'auto']} />
                                    <Tooltip
                                        formatter={(value: number) => [`$${value}B`, '推理收入']}
                                        labelFormatter={(label) => label}
                                        contentStyle={{ fontSize: '12px', borderRadius: '8px' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="revenue"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        fill="url(#revenueGradient)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* 右侧: 成本端 */}
                    <div className="rounded-xl p-5 bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-lg bg-orange-500 flex items-center justify-center">
                                    <Server className="w-4 h-4 text-white" />
                                </div>
                                <span className="font-semibold text-gray-800">成本端</span>
                            </div>
                            {summary.latest_depreciation_growth >= 0 ? (
                                <ArrowUpRight className="w-5 h-5 text-orange-500" />
                            ) : (
                                <ArrowDownRight className="w-5 h-5 text-emerald-500" />
                            )}
                        </div>

                        {/* 绝对值 */}
                        <div className="mb-3">
                            <div className="text-3xl font-bold text-gray-900">
                                ${summary.latest_depreciation_b}B
                            </div>
                            <div className="text-sm text-gray-500">
                                {summary.latest_quarter} AI资产折旧
                            </div>
                        </div>

                        {/* 趋势值 - 明确标注比较基准 */}
                        <div className="p-3 bg-white/60 rounded-lg">
                            <div className="flex items-baseline justify-between">
                                <div>
                                    <span className={`text-2xl font-bold ${summary.latest_depreciation_growth <= 10 ? 'text-emerald-600' :
                                            summary.latest_depreciation_growth <= 20 ? 'text-orange-600' : 'text-red-600'
                                        }`}>
                                        {summary.latest_depreciation_growth >= 0 ? '+' : ''}{summary.latest_depreciation_growth}%
                                    </span>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-gray-500">环比增速</div>
                                    <div className="text-xs text-gray-400">vs {prevQuarter}</div>
                                </div>
                            </div>
                        </div>

                        {/* 面积图 */}
                        <div className="h-28 mt-4 -mx-2">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                                    <defs>
                                        <linearGradient id="depreciationGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                                    <XAxis
                                        dataKey="quarter"
                                        tick={{ fontSize: 10, fill: '#6b7280' }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <YAxis hide domain={['auto', 'auto']} />
                                    <Tooltip
                                        formatter={(value: number) => [`$${value}B`, 'AI资产折旧']}
                                        labelFormatter={(label) => label}
                                        contentStyle={{ fontSize: '12px', borderRadius: '8px' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="depreciation"
                                        stroke="#f97316"
                                        strokeWidth={2}
                                        fill="url(#depreciationGradient)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* 净差值汇总 */}
                <div className="rounded-xl p-5 bg-gradient-to-r from-slate-50 to-slate-100 border border-slate-200">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${summary.latest_net_difference >= 5 ? 'bg-gradient-to-br from-emerald-400 to-green-500' :
                                    summary.latest_net_difference >= 0 ? 'bg-gradient-to-br from-blue-400 to-indigo-500' :
                                        'bg-gradient-to-br from-red-400 to-rose-500'
                                }`}>
                                {summary.latest_net_difference >= 0 ? (
                                    <TrendingUp className="w-7 h-7 text-white" />
                                ) : (
                                    <TrendingDown className="w-7 h-7 text-white" />
                                )}
                            </div>
                            <div>
                                <div className="text-sm text-gray-500 mb-1">
                                    净差值 <span className="text-xs">(收入增速 - 成本增速)</span>
                                </div>
                                <div className={`text-3xl font-bold ${summary.latest_net_difference >= 5 ? 'text-emerald-600' :
                                        summary.latest_net_difference >= 0 ? 'text-blue-600' : 'text-red-600'
                                    }`}>
                                    {summary.latest_net_difference >= 0 ? '+' : ''}{summary.latest_net_difference}%
                                </div>
                            </div>
                        </div>

                        <div className="text-right">
                            <div className="text-sm text-gray-500 mb-1">近4季度平均</div>
                            <div className={`text-2xl font-semibold ${summary.avg_net_4q >= 0 ? 'text-emerald-600' : 'text-red-600'
                                }`}>
                                {summary.avg_net_4q >= 0 ? '+' : ''}{summary.avg_net_4q}%
                            </div>
                        </div>
                    </div>

                    {/* 解读 */}
                    <div className="mt-4 pt-4 border-t border-slate-200">
                        <div className="flex items-start gap-3">
                            <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${summary.latest_net_difference >= 5 ? 'bg-emerald-100' :
                                    summary.latest_net_difference >= 0 ? 'bg-blue-100' : 'bg-red-100'
                                }`}>
                                {summary.latest_net_difference >= 0 ? (
                                    <CheckCircle className={`w-4 h-4 ${summary.latest_net_difference >= 5 ? 'text-emerald-600' : 'text-blue-600'
                                        }`} />
                                ) : (
                                    <AlertCircle className="w-4 h-4 text-red-600" />
                                )}
                            </div>
                            <div className="text-sm text-gray-600">
                                {summary.latest_net_difference >= 5 ? (
                                    <>
                                        <span className="font-medium text-emerald-700">
                                            收入环比+{summary.latest_revenue_growth}% &gt; 成本环比+{summary.latest_depreciation_growth}%
                                        </span>
                                        <p className="text-gray-500 mt-1">
                                            挣钱速度显著超过花钱速度，AI 投资正在产生正向回报
                                        </p>
                                    </>
                                ) : summary.latest_net_difference >= 0 ? (
                                    <>
                                        <span className="font-medium text-blue-700">
                                            收入环比+{summary.latest_revenue_growth}% ≈ 成本环比+{summary.latest_depreciation_growth}%
                                        </span>
                                        <p className="text-gray-500 mt-1">
                                            收支增速基本持平，投资回收期较长
                                        </p>
                                    </>
                                ) : (
                                    <>
                                        <span className="font-medium text-red-700">
                                            成本环比+{summary.latest_depreciation_growth}% &gt; 收入环比+{summary.latest_revenue_growth}%
                                        </span>
                                        <p className="text-gray-500 mt-1">
                                            花钱速度超过挣钱速度，需关注投资可持续性
                                        </p>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
