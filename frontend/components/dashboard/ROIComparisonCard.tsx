'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Scale, ArrowUpRight, ArrowDownRight, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, ComposedChart, Bar } from 'recharts';

interface ComparisonData {
    quarter: string;
    revenueGrowth: number;  // 收入增速 %
    costGrowth: number;     // 成本增速 %
    netMargin: number;      // 净差值（收入增速 - 成本增速）
    coverageRatio: number;  // 覆盖率
    efficiencyIndex: number; // 效率指数
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ROIComparisonCard() {
    const [data, setData] = useState<ComparisonData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [sustainabilityScore, setSustainabilityScore] = useState<number>(0);
    const [trend, setTrend] = useState<'improving' | 'stable' | 'declining'>('stable');

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 获取收入端数据
                const revenueRes = await fetch(`${API_BASE}/api/v1/financials/ai-roi`);
                const revenueData = await revenueRes.json();

                // 获取成本端数据
                const costRes = await fetch(`${API_BASE}/api/v1/financials/gpu-efficiency`);
                const costData = await costRes.json();

                if (revenueData.success && costData.success) {
                    const coverageSeries = revenueData.data.inference_coverage.trend_series;
                    const efficiencySeries = costData.data.pflops_series;

                    // 合并数据，计算增速对比
                    const combined: ComparisonData[] = [];

                    for (let i = 0; i < coverageSeries.length; i++) {
                        const quarter = coverageSeries[i].quarter;
                        const coverageRatio = coverageSeries[i].coverage_ratio;
                        const efficiency = efficiencySeries.find((e: any) => e.quarter === quarter);

                        // 计算环比增速
                        const prevCoverage = i > 0 ? coverageSeries[i - 1].coverage_ratio : coverageRatio;
                        const prevEfficiency = i > 0 && efficiency ?
                            (efficiencySeries.find((e: any) => e.quarter === coverageSeries[i - 1]?.quarter)?.index || 100) :
                            (efficiency?.index || 100);

                        // 收入增速 = 覆盖率变化（覆盖率上升说明收入相对成本在增加）
                        const revenueGrowth = ((coverageRatio - prevCoverage) / prevCoverage) * 100;

                        // 成本增速 = 效率指数变化的负值（效率上升说明成本在下降）
                        const costGrowth = efficiency ?
                            -((efficiency.index - prevEfficiency) / prevEfficiency) * 100 : 0;

                        combined.push({
                            quarter,
                            revenueGrowth: Math.round(revenueGrowth * 10) / 10,
                            costGrowth: Math.round(costGrowth * 10) / 10,
                            netMargin: Math.round((revenueGrowth - costGrowth) * 10) / 10,
                            coverageRatio,
                            efficiencyIndex: efficiency?.index || 100,
                        });
                    }

                    setData(combined);

                    // 计算可持续性评分（基于最近4季度）
                    const recent = combined.slice(-4);
                    const avgNetMargin = recent.reduce((a, b) => a + b.netMargin, 0) / recent.length;
                    const latestCoverage = recent[recent.length - 1]?.coverageRatio || 0;

                    // 评分 = 覆盖率权重 * 50 + 净差值权重 * 50
                    const score = Math.min(100, Math.max(0,
                        (latestCoverage * 40) + (avgNetMargin > 0 ? 30 : 0) + (avgNetMargin * 2)
                    ));
                    setSustainabilityScore(Math.round(score));

                    // 判断趋势
                    if (avgNetMargin > 2) {
                        setTrend('improving');
                    } else if (avgNetMargin < -2) {
                        setTrend('declining');
                    } else {
                        setTrend('stable');
                    }
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

    if (error) {
        return (
            <div className="bg-red-50 rounded-xl shadow-sm border border-red-100 p-6">
                <p className="text-red-600">{error}</p>
            </div>
        );
    }

    const latestData = data[data.length - 1];
    const trendConfig = {
        improving: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: '可持续改善中' },
        stable: { icon: Scale, color: 'text-yellow-600', bg: 'bg-yellow-100', label: '趋势平稳' },
        declining: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100', label: '需关注' },
    };
    const TrendIcon = trendConfig[trend].icon;

    return (
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl shadow-sm border border-indigo-100 p-6">
            {/* 标题 */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Scale className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-lg font-semibold text-gray-900">收入 vs 成本 趋势对比</h3>
                </div>
                <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${trendConfig[trend].bg}`}>
                    <TrendIcon className={`w-4 h-4 ${trendConfig[trend].color}`} />
                    <span className={`text-sm font-medium ${trendConfig[trend].color}`}>
                        {trendConfig[trend].label}
                    </span>
                </div>
            </div>

            {/* 核心洞察 */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                {/* 可持续性评分 */}
                <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-sm text-gray-500 mb-1">可持续性评分</div>
                    <div className="flex items-baseline gap-2">
                        <span className={`text-3xl font-bold ${sustainabilityScore >= 70 ? 'text-green-600' :
                                sustainabilityScore >= 50 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                            {sustainabilityScore}
                        </span>
                        <span className="text-gray-400">/100</span>
                    </div>
                    <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full ${sustainabilityScore >= 70 ? 'bg-green-500' :
                                    sustainabilityScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                }`}
                            style={{ width: `${sustainabilityScore}%` }}
                        />
                    </div>
                </div>

                {/* 挣钱速度 */}
                <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-sm text-gray-500 mb-1">收入增速 (环比)</div>
                    <div className="flex items-center gap-2">
                        <span className={`text-2xl font-bold ${latestData?.revenueGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {latestData?.revenueGrowth >= 0 ? '+' : ''}{latestData?.revenueGrowth || 0}%
                        </span>
                        {latestData?.revenueGrowth >= 0 ?
                            <ArrowUpRight className="w-5 h-5 text-green-500" /> :
                            <ArrowDownRight className="w-5 h-5 text-red-500" />
                        }
                    </div>
                    <div className="text-xs text-gray-400 mt-1">推理覆盖率变化</div>
                </div>

                {/* 花钱速度 */}
                <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-sm text-gray-500 mb-1">成本增速 (环比)</div>
                    <div className="flex items-center gap-2">
                        <span className={`text-2xl font-bold ${latestData?.costGrowth <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {latestData?.costGrowth >= 0 ? '+' : ''}{latestData?.costGrowth || 0}%
                        </span>
                        {latestData?.costGrowth <= 0 ?
                            <ArrowDownRight className="w-5 h-5 text-green-500" /> :
                            <ArrowUpRight className="w-5 h-5 text-red-500" />
                        }
                    </div>
                    <div className="text-xs text-gray-400 mt-1">算力成本变化 (负值=省钱)</div>
                </div>
            </div>

            {/* 对比图表 */}
            <div className="bg-white rounded-lg p-4 shadow-sm">
                <h4 className="text-sm font-medium text-gray-600 mb-3">
                    💡 关键问题：挣钱速度是否超过花钱速度？
                </h4>
                <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="quarter" tick={{ fill: '#6b7280', fontSize: 10 }} />
                            <YAxis
                                yAxisId="left"
                                domain={[-20, 20]}
                                tick={{ fill: '#6b7280', fontSize: 10 }}
                                tickFormatter={(v) => `${v}%`}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                                formatter={(value: number, name: string) => {
                                    const labels: Record<string, string> = {
                                        revenueGrowth: '收入增速',
                                        costGrowth: '成本增速',
                                        netMargin: '净差值'
                                    };
                                    return [`${value}%`, labels[name] || name];
                                }}
                            />
                            <Legend
                                formatter={(value) => {
                                    const labels: Record<string, string> = {
                                        revenueGrowth: '💰 收入增速',
                                        costGrowth: '💸 成本增速',
                                        netMargin: '📊 净差值'
                                    };
                                    return labels[value] || value;
                                }}
                            />
                            {/* 净差值柱状图 - 背景 */}
                            <Bar
                                yAxisId="left"
                                dataKey="netMargin"
                                fill="#818cf8"
                                opacity={0.3}
                                radius={[2, 2, 0, 0]}
                            />
                            {/* 收入增速线 */}
                            <Line
                                yAxisId="left"
                                type="monotone"
                                dataKey="revenueGrowth"
                                stroke="#10b981"
                                strokeWidth={2}
                                dot={{ fill: '#10b981', r: 4 }}
                            />
                            {/* 成本增速线 */}
                            <Line
                                yAxisId="left"
                                type="monotone"
                                dataKey="costGrowth"
                                stroke="#ef4444"
                                strokeWidth={2}
                                dot={{ fill: '#ef4444', r: 4 }}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>

                {/* 解读 */}
                <div className="mt-4 p-3 bg-indigo-50 rounded-lg">
                    <div className="flex items-start gap-2">
                        <span className="text-lg">📈</span>
                        <div className="text-sm text-gray-700">
                            <strong>解读：</strong>
                            {latestData && latestData.netMargin > 0 ? (
                                <span className="text-green-700">
                                    绿线(收入)在红线(成本)上方 → <strong>挣钱比花钱快</strong>，
                                    净差值 +{latestData.netMargin}%，投资正在回本！
                                </span>
                            ) : latestData && latestData.netMargin < 0 ? (
                                <span className="text-red-700">
                                    红线(成本)在绿线(收入)上方 → <strong>花钱比挣钱快</strong>，
                                    净差值 {latestData.netMargin}%，需警惕投资回报！
                                </span>
                            ) : (
                                <span className="text-yellow-700">
                                    收入与成本增速接近 → <strong>盈亏平衡</strong>，保持观察
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
