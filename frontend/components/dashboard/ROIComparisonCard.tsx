'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Scale, DollarSign, Server, AlertCircle, CheckCircle, HelpCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

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
            <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl shadow-sm border border-indigo-100 p-6">
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

    // 趋势配置
    const trendConfigs: Record<string, { icon: typeof CheckCircle; color: string; bg: string }> = {
        strong_growth: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100' },
        sustainable: { icon: CheckCircle, color: 'text-blue-600', bg: 'bg-blue-100' },
        attention: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-100' },
        risk: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-100' },
    };
    const trendConfig = trendConfigs[summary.trend] || trendConfigs.attention;
    const TrendIcon = trendConfig.icon;

    // 为图表准备数据
    const revenueChartData = quarterly_data.map(q => ({
        quarter: q.quarter.replace('20', ''),
        value: q.revenue_growth,
    }));

    const depreciationChartData = quarterly_data.map(q => ({
        quarter: q.quarter.replace('20', ''),
        value: q.depreciation_growth,
    }));

    return (
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl shadow-sm border border-indigo-100 p-6">
            {/* 标题行 */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Scale className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-lg font-semibold text-gray-900">挣钱速度 vs 花钱速度</h3>
                    <button
                        onClick={() => setShowDefinitions(!showDefinitions)}
                        className="text-gray-400 hover:text-gray-600"
                        title="查看定义"
                    >
                        <HelpCircle className="w-4 h-4" />
                    </button>
                </div>
                <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${trendConfig.bg}`}>
                    <TrendIcon className={`w-4 h-4 ${trendConfig.color}`} />
                    <span className={`text-sm font-medium ${trendConfig.color}`}>
                        {summary.trend_label}
                    </span>
                </div>
            </div>

            {/* 定义说明 (可折叠) */}
            {showDefinitions && (
                <div className="mb-6 p-4 bg-white/80 rounded-lg text-sm text-gray-600 space-y-2">
                    <p><strong>📈 收入增速</strong>: {definitions.revenue_growth}</p>
                    <p><strong>📉 成本增速</strong>: {definitions.depreciation_growth}</p>
                    <p><strong>💡 净差值</strong>: {definitions.net_difference}</p>
                    <p className="text-xs text-gray-500 mt-2">
                        数据来源: OpenAI + Anthropic 季度数据 (The Information 估算)
                    </p>
                </div>
            )}

            {/* 核心对比：两列并排 */}
            <div className="grid grid-cols-2 gap-6 mb-6">
                {/* 左侧: 收入端 */}
                <div className="bg-white rounded-xl p-4 shadow-sm border border-green-100">
                    <div className="flex items-center gap-2 mb-3">
                        <DollarSign className="w-5 h-5 text-green-500" />
                        <span className="font-medium text-gray-700">收入增速</span>
                    </div>

                    {/* 最新值 */}
                    <div className="flex items-baseline gap-2 mb-4">
                        <span className={`text-3xl font-bold ${summary.latest_revenue_growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {summary.latest_revenue_growth > 0 ? '+' : ''}{summary.latest_revenue_growth}%
                        </span>
                        <span className="text-sm text-gray-500">/{summary.latest_quarter}</span>
                    </div>

                    {/* 绝对值 */}
                    <div className="text-sm text-gray-500 mb-3">
                        推理收入: ${summary.latest_revenue_b}B / 季度
                    </div>

                    {/* 增速柱状图 */}
                    <div className="h-24">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={revenueChartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                                <XAxis dataKey="quarter" tick={{ fontSize: 9, fill: '#9ca3af' }} />
                                <YAxis hide domain={[0, 'auto']} />
                                <Tooltip
                                    formatter={(value: number) => [`${value}%`, '增速']}
                                    labelFormatter={(label) => `${label}`}
                                    contentStyle={{ fontSize: '12px' }}
                                />
                                <ReferenceLine y={0} stroke="#e5e7eb" />
                                <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                                    {revenueChartData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.value >= 0 ? '#22c55e' : '#ef4444'}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 右侧: 成本端 */}
                <div className="bg-white rounded-xl p-4 shadow-sm border border-red-100">
                    <div className="flex items-center gap-2 mb-3">
                        <Server className="w-5 h-5 text-red-500" />
                        <span className="font-medium text-gray-700">成本增速</span>
                    </div>

                    {/* 最新值 */}
                    <div className="flex items-baseline gap-2 mb-4">
                        <span className={`text-3xl font-bold ${summary.latest_depreciation_growth <= 0 ? 'text-green-600' : 'text-orange-600'}`}>
                            {summary.latest_depreciation_growth >= 0 ? '+' : ''}{summary.latest_depreciation_growth}%
                        </span>
                        <span className="text-sm text-gray-500">/{summary.latest_quarter}</span>
                    </div>

                    {/* 绝对值 */}
                    <div className="text-sm text-gray-500 mb-3">
                        AI资产折旧: ${summary.latest_depreciation_b}B / 季度
                    </div>

                    {/* 增速柱状图 */}
                    <div className="h-24">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={depreciationChartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                                <XAxis dataKey="quarter" tick={{ fontSize: 9, fill: '#9ca3af' }} />
                                <YAxis hide domain={[0, 'auto']} />
                                <Tooltip
                                    formatter={(value: number) => [`${value}%`, '增速']}
                                    labelFormatter={(label) => `${label}`}
                                    contentStyle={{ fontSize: '12px' }}
                                />
                                <ReferenceLine y={0} stroke="#e5e7eb" />
                                <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                                    {depreciationChartData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.value >= 20 ? '#f97316' : entry.value >= 10 ? '#facc15' : '#22c55e'}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* 净差值汇总 */}
            <div className="bg-white rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${summary.latest_net_difference >= 5 ? 'bg-green-100' :
                                summary.latest_net_difference >= 0 ? 'bg-blue-100' : 'bg-red-100'
                            }`}>
                            {summary.latest_net_difference >= 0 ? (
                                <TrendingUp className={`w-6 h-6 ${summary.latest_net_difference >= 5 ? 'text-green-600' : 'text-blue-600'
                                    }`} />
                            ) : (
                                <TrendingDown className="w-6 h-6 text-red-600" />
                            )}
                        </div>
                        <div>
                            <div className="text-sm text-gray-500">净差值 (收入增速 - 成本增速)</div>
                            <div className={`text-2xl font-bold ${summary.latest_net_difference >= 5 ? 'text-green-600' :
                                    summary.latest_net_difference >= 0 ? 'text-blue-600' : 'text-red-600'
                                }`}>
                                {summary.latest_net_difference >= 0 ? '+' : ''}{summary.latest_net_difference}%
                            </div>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-sm text-gray-500">近4季度平均</div>
                        <div className={`text-xl font-semibold ${summary.avg_net_4q >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                            {summary.avg_net_4q >= 0 ? '+' : ''}{summary.avg_net_4q}%
                        </div>
                    </div>
                </div>

                {/* 解读 */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-sm text-gray-600">
                        {summary.latest_net_difference >= 5 ? (
                            <>
                                <span className="text-green-600 font-medium">✓ 收入增速 ({summary.latest_revenue_growth}%) 显著超过成本增速 ({summary.latest_depreciation_growth}%)</span>
                                <br />
                                <span className="text-gray-500">→ AI 投资正在产生正向回报，商业模式可持续</span>
                            </>
                        ) : summary.latest_net_difference >= 0 ? (
                            <>
                                <span className="text-blue-600 font-medium">○ 收入增速 ({summary.latest_revenue_growth}%) 略高于成本增速 ({summary.latest_depreciation_growth}%)</span>
                                <br />
                                <span className="text-gray-500">→ 投资回收期较长，需持续观察</span>
                            </>
                        ) : (
                            <>
                                <span className="text-red-600 font-medium">⚠ 成本增速 ({summary.latest_depreciation_growth}%) 超过收入增速 ({summary.latest_revenue_growth}%)</span>
                                <br />
                                <span className="text-gray-500">→ 花钱比挣钱快，需关注投资可持续性</span>
                            </>
                        )}
                    </p>
                </div>
            </div>
        </div>
    );
}
