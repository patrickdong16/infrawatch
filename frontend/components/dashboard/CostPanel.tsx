'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Cpu, Zap, Server } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import MetricTooltip from '@/components/ui/MetricTooltip';

interface GPUEfficiencyData {
    current: {
        pflops_index: number;
        task_index: number;
    };
    pflops_series: {
        quarter: string;
        index: number;
        best_cost_per_pflops: number;
    }[];
    base_period: string;
}

export default function CostPanel() {
    const [data, setData] = useState<GPUEfficiencyData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiUrl}/api/v1/financials/gpu-efficiency`);
                const result = await res.json();

                if (result.success) {
                    setData(result.data);
                }
            } catch (err) {
                console.error('Failed to fetch cost data:', err);
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

    const improvement = data.current.pflops_index - 100;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center gap-2 mb-4">
                <Server className="w-5 h-5 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">成本端分析</h3>
            </div>

            {/* 两个子指标 */}
            <div className="grid grid-cols-2 gap-4 mb-4">
                {/* PFLOPS 效率 */}
                <div className="bg-purple-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-yellow-600" />
                        <MetricTooltip content="每PFLOPS算力的云端租赁成本效率。以2024Q1为基准(=100)，指数越高表示同等性能的成本越低。">
                            <span className="text-sm font-medium text-gray-700">PFLOPS 效率</span>
                        </MetricTooltip>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-gray-900">{data.current.pflops_index.toFixed(0)}</span>
                        <span className={`text-sm flex items-center ${improvement > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {improvement > 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                            {improvement > 0 ? '+' : ''}{improvement.toFixed(0)}%
                        </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">vs {data.base_period} 基准=100</p>
                </div>

                {/* 任务成本效率 */}
                <div className="bg-cyan-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-4 h-4 text-blue-600" />
                        <MetricTooltip content="执行标准AI推理任务(如1M tokens)的成本效率。考虑了GPU利用率和模型效率的综合指标。">
                            <span className="text-sm font-medium text-gray-700">任务成本效率</span>
                        </MetricTooltip>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-gray-900">{data.current.task_index.toFixed(0)}</span>
                        <span className={`text-sm flex items-center ${data.current.task_index > 100 ? 'text-green-600' : 'text-red-600'}`}>
                            {data.current.task_index > 100 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                            {data.current.task_index > 100 ? '+' : ''}{(data.current.task_index - 100).toFixed(0)}%
                        </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">标准推理任务</p>
                </div>
            </div>

            {/* 成本历史 */}
            <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-600 mb-2">每 PFLOPS 成本趋势</h4>
                <div className="space-y-2">
                    {data.pflops_series.slice(-4).map((s, i) => (
                        <div key={s.quarter} className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 w-16">{s.quarter}</span>
                            <div className="flex-1 bg-gray-100 rounded-full h-2">
                                <div
                                    className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                                    style={{ width: `${Math.min((s.index / 180) * 100, 100)}%` }}
                                ></div>
                            </div>
                            <span className="text-xs font-medium text-gray-700 w-12">${s.best_cost_per_pflops}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 趋势图 */}
            <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.pflops_series}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="quarter" tick={{ fill: '#6b7280', fontSize: 10 }} />
                        <YAxis domain={[80, 180]} tick={{ fill: '#6b7280', fontSize: 10 }} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                            formatter={(value: number) => [value.toFixed(1), '效率指数']}
                        />
                        <ReferenceLine y={100} stroke="#9ca3af" strokeDasharray="5 5" />
                        <Line type="monotone" dataKey="index" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
