'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Building2, Cloud, Target, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';

interface InferenceCompany {
    company: string;
    category: string;
    latest_quarter: string;
    coverage_ratio: number;
    inference_revenue_b: number;
    asset_depreciation_b: number;
    trend: string;
}

interface CapitalIntensityCompany {
    ticker: string;
    name: string;
    quarter: string;
    revenue_b: number;
    capex_b: number;
    capital_intensity: number;
}

interface AIROIData {
    core_question: string;
    overall_verdict: {
        trend: string;
        description: string;
        current_coverage: number;
        previous_coverage: number;
        change: number;
    };
    inference_coverage: {
        title: string;
        description: string;
        perspective: string;
        industry_average: number;
        companies: InferenceCompany[];
        trend_series: { quarter: string; coverage_ratio: number; threshold: number }[];
    };
    capital_intensity: {
        title: string;
        description: string;
        perspective: string;
        overall: number;
        companies: CapitalIntensityCompany[];
    };
}

export default function AIROICard() {
    const [data, setData] = useState<AIROIData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/v1/financials/ai-roi`);
                const result = await response.json();

                if (result.success) {
                    setData(result.data);
                } else {
                    setError('Failed to fetch AI ROI data');
                }
            } catch (err) {
                setError('Network error');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-slate-700 rounded w-3/4"></div>
                    <div className="h-32 bg-slate-700 rounded"></div>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                <div className="text-red-400">加载失败: {error}</div>
            </div>
        );
    }

    const verdict = data.overall_verdict;
    const trendColor = verdict.trend === 'sustainable' ? 'text-green-400' :
        verdict.trend === 'improving' ? 'text-blue-400' :
            verdict.trend === 'balanced' ? 'text-yellow-400' : 'text-red-400';
    const trendBg = verdict.trend === 'sustainable' ? 'bg-green-500/10' :
        verdict.trend === 'improving' ? 'bg-blue-500/10' :
            verdict.trend === 'balanced' ? 'bg-yellow-500/10' : 'bg-red-500/10';

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 space-y-6">
            {/* 标题和核心问题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Target className="w-5 h-5 text-blue-400" />
                        AI 投资回报分析
                    </h3>
                    <p className="text-sm text-slate-400 mt-1">{data.core_question}</p>
                </div>
                <div className={`px-3 py-1 rounded-full ${trendBg}`}>
                    <span className={`text-sm font-medium ${trendColor}`}>
                        {verdict.trend === 'sustainable' ? '✅ 可持续' :
                            verdict.trend === 'improving' ? '📈 改善中' :
                                verdict.trend === 'balanced' ? '⚖️ 平衡' : '⚠️ 需关注'}
                    </span>
                </div>
            </div>

            {/* 核心判定 */}
            <div className={`p-4 rounded-lg ${trendBg} border border-slate-600`}>
                <p className={`text-sm ${trendColor}`}>{verdict.description}</p>
                <div className="flex items-center gap-4 mt-2">
                    <span className="text-white font-semibold text-lg">
                        覆盖率: {(verdict.current_coverage * 100).toFixed(0)}%
                    </span>
                    <span className={`text-sm flex items-center gap-1 ${verdict.change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {verdict.change > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {verdict.change > 0 ? '+' : ''}{(verdict.change * 100).toFixed(0)}pp QoQ
                    </span>
                </div>
            </div>

            {/* 趋势图 */}
            <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.inference_coverage.trend_series}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="quarter" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                        <YAxis
                            domain={[0, 1.5]}
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                            formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, '覆盖率']}
                        />
                        <Legend />
                        <ReferenceLine
                            y={1}
                            stroke="#f59e0b"
                            strokeDasharray="5 5"
                            label={{ value: '盈亏平衡', fill: '#f59e0b', fontSize: 12 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="coverage_ratio"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={{ fill: '#3b82f6' }}
                            name="行业覆盖率"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* 两个视角 */}
            <div className="grid grid-cols-2 gap-4">
                {/* 推理资产覆盖率 */}
                <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <Building2 className="w-4 h-4 text-purple-400" />
                        <span className="text-sm font-medium text-white">
                            {data.inference_coverage.title}
                        </span>
                    </div>
                    <p className="text-xs text-slate-400 mb-3">{data.inference_coverage.perspective}</p>

                    {data.inference_coverage.companies.map((c) => (
                        <div key={c.company} className="flex justify-between items-center py-2 border-t border-slate-700">
                            <span className="text-sm text-slate-300">{c.company}</span>
                            <div className="flex items-center gap-2">
                                <span className={`text-sm font-medium ${c.coverage_ratio >= 1 ? 'text-green-400' : 'text-yellow-400'}`}>
                                    {(c.coverage_ratio * 100).toFixed(0)}%
                                </span>
                                {c.trend === 'improving' && <TrendingUp className="w-3 h-3 text-green-400" />}
                                {c.trend === 'declining' && <TrendingDown className="w-3 h-3 text-red-400" />}
                            </div>
                        </div>
                    ))}
                </div>

                {/* 资本密集度 */}
                <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <Cloud className="w-4 h-4 text-cyan-400" />
                        <span className="text-sm font-medium text-white">
                            {data.capital_intensity.title}
                        </span>
                    </div>
                    <p className="text-xs text-slate-400 mb-3">{data.capital_intensity.perspective}</p>

                    {data.capital_intensity.companies.map((c) => (
                        <div key={c.ticker} className="flex justify-between items-center py-2 border-t border-slate-700">
                            <span className="text-sm text-slate-300">{c.name}</span>
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-blue-400">
                                    {c.capital_intensity}%
                                </span>
                                <span className="text-xs text-slate-500">
                                    ${c.capex_b}B
                                </span>
                            </div>
                        </div>
                    ))}

                    <div className="flex justify-between items-center pt-2 mt-2 border-t border-slate-600">
                        <span className="text-sm font-medium text-white">整体</span>
                        <span className="text-sm font-bold text-cyan-400">{data.capital_intensity.overall}%</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
