'use client';

import { useState, useEffect } from 'react';
import { Cpu, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';

interface GPUEfficiencyData {
    title: string;
    description: string;
    base_period: string;
    base_index: number;
    current: {
        pflops_index: number;
        task_index: number;
        interpretation: string;
    };
    pflops_series: {
        quarter: string;
        index: number;
        best_cost_per_pflops: number;
        avg_cost_per_pflops: number;
    }[];
    task_series: {
        quarter: string;
        index: number;
        best_gpu: string;
        cost_usd: number;
    }[];
}

export default function GPUEfficiencyCard() {
    const [data, setData] = useState<GPUEfficiencyData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/v1/financials/gpu-efficiency`);
                const result = await response.json();

                if (result.success) {
                    setData(result.data);
                } else {
                    setError('Failed to fetch GPU efficiency data');
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

    const improvement = data.current.pflops_index - 100;
    const isImproved = improvement > 0;

    return (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 space-y-4">
            {/* 标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Cpu className="w-5 h-5 text-green-400" />
                        {data.title}
                    </h3>
                    <p className="text-sm text-slate-400 mt-1">{data.description}</p>
                </div>
            </div>

            {/* 当前指数 */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm text-slate-400">PFLOPS 效率</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-white">{data.current.pflops_index}</span>
                        <span className={`text-sm flex items-center gap-1 ${isImproved ? 'text-green-400' : 'text-red-400'}`}>
                            {isImproved ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {isImproved ? '+' : ''}{improvement.toFixed(1)}%
                        </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">vs {data.base_period} 基准</p>
                </div>

                <div className="bg-slate-900/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-sm text-slate-400">任务成本效率</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-white">{data.current.task_index}</span>
                        <span className={`text-sm flex items-center gap-1 ${data.current.task_index > 100 ? 'text-green-400' : 'text-red-400'}`}>
                            {data.current.task_index > 100 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {data.current.task_index > 100 ? '+' : ''}{(data.current.task_index - 100).toFixed(1)}%
                        </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">标准推理任务</p>
                </div>
            </div>

            {/* 效率趋势图 */}
            <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.pflops_series}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="quarter" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                        <YAxis
                            domain={[80, 180]}
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                            formatter={(value: number, name: string) => [
                                name === 'index' ? value : `$${value}`,
                                name === 'index' ? '效率指数' : '$/PFLOPS'
                            ]}
                        />
                        <Legend />
                        <ReferenceLine
                            y={100}
                            stroke="#64748b"
                            strokeDasharray="5 5"
                            label={{ value: '基准=100', fill: '#64748b', fontSize: 10 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="index"
                            stroke="#22c55e"
                            strokeWidth={2}
                            dot={{ fill: '#22c55e' }}
                            name="效率指数"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* 解释 */}
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg px-4 py-2">
                <p className="text-sm text-green-400">{data.current.interpretation}</p>
            </div>
        </div>
    );
}
