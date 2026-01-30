'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Building2, Cloud, DollarSign } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import MetricTooltip from '@/components/ui/MetricTooltip';

interface InferenceCompany {
    company: string;
    coverage_ratio: number;
    trend: string;
}

interface CapitalIntensityCompany {
    name: string;
    capital_intensity: number;
    capex_b: number;
}

interface RevenueData {
    inference_coverage: {
        industry_average: number;
        companies: InferenceCompany[];
        trend_series: { quarter: string; coverage_ratio: number }[];
    };
    capital_intensity: {
        overall: number;
        companies: CapitalIntensityCompany[];
    };
}

export default function RevenuePanel() {
    const [data, setData] = useState<RevenueData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiUrl}/api/v1/financials/ai-roi`);
                const result = await res.json();

                if (result.success) {
                    setData({
                        inference_coverage: result.data.inference_coverage,
                        capital_intensity: result.data.capital_intensity,
                    });
                }
            } catch (err) {
                console.error('Failed to fetch revenue data:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="animate-pulse h-48 bg-gray-100 rounded"></div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <p className="text-gray-400">加载失败</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center gap-2 mb-4">
                <DollarSign className="w-5 h-5 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">收入端分析</h3>
            </div>

            {/* 两个子指标 */}
            <div className="grid grid-cols-2 gap-4 mb-4">
                {/* 推理覆盖率 */}
                <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Building2 className="w-4 h-4 text-purple-600" />
                        <MetricTooltip content="AI模型公司(如OpenAI/Anthropic)的推理收入能否覆盖GPU等AI资产的年化折旧成本。>100%表示盈利能力可持续。">
                            <span className="text-sm font-medium text-gray-700">推理覆盖率</span>
                        </MetricTooltip>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                        {(data.inference_coverage.industry_average * 100).toFixed(0)}%
                    </div>
                    <p className="text-xs text-gray-500 mt-1">行业平均 (收入/折旧)</p>

                    <div className="mt-3 space-y-1">
                        {data.inference_coverage.companies.map(c => (
                            <div key={c.company} className="flex justify-between text-sm">
                                <span className="text-gray-600">{c.company}</span>
                                <span className={c.coverage_ratio >= 1 ? 'text-green-600' : 'text-yellow-600'}>
                                    {(c.coverage_ratio * 100).toFixed(0)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 资本密集度 */}
                <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Cloud className="w-4 h-4 text-cyan-600" />
                        <MetricTooltip content="云厂商AI相关资本支出占总营收的比例。高密集度意味着需要更多收入来回本，但也反映对AI基建的投入力度。">
                            <span className="text-sm font-medium text-gray-700">资本密集度</span>
                        </MetricTooltip>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                        {data.capital_intensity.overall}%
                    </div>
                    <p className="text-xs text-gray-500 mt-1">CapEx / 总收入</p>

                    <div className="mt-3 space-y-1">
                        {data.capital_intensity.companies.map(c => (
                            <div key={c.name} className="flex justify-between text-sm">
                                <span className="text-gray-600">{c.name}</span>
                                <span className="text-blue-600">{c.capital_intensity}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 趋势图 */}
            <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.inference_coverage.trend_series}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="quarter" tick={{ fill: '#6b7280', fontSize: 11 }} />
                        <YAxis
                            domain={[0, 1.5]}
                            tick={{ fill: '#6b7280', fontSize: 11 }}
                            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                            formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, '覆盖率']}
                        />
                        <ReferenceLine y={1} stroke="#f59e0b" strokeDasharray="5 5" label={{ value: '盈亏平衡', fill: '#f59e0b', fontSize: 10 }} />
                        <Line type="monotone" dataKey="coverage_ratio" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} name="覆盖率" />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
