'use client';

import { useState, useEffect } from 'react';
import { Target, TrendingUp, TrendingDown, Zap, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import MetricTooltip from '@/components/ui/MetricTooltip';

interface HeroData {
    verdict: 'sustainable' | 'improving' | 'balanced' | 'concerning';
    coverage_ratio: number;
    coverage_change: number;
    efficiency_index: number;
    efficiency_change: number;
    stage: string;
    confidence: string;
    summary: string;
}

export default function HeroCard() {
    const [data, setData] = useState<HeroData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

                // 并行获取 ROI 和 GPU 效率数据
                const [roiRes, gpuRes] = await Promise.all([
                    fetch(`${apiUrl}/api/v1/financials/ai-roi`),
                    fetch(`${apiUrl}/api/v1/financials/gpu-efficiency`)
                ]);

                const [roiData, gpuData] = await Promise.all([
                    roiRes.json(),
                    gpuRes.json()
                ]);

                if (roiData.success && gpuData.success) {
                    const roi = roiData.data;
                    const gpu = gpuData.data;

                    setData({
                        verdict: roi.overall_verdict.trend,
                        coverage_ratio: roi.overall_verdict.current_coverage,
                        coverage_change: roi.overall_verdict.change,
                        efficiency_index: gpu.current.pflops_index,
                        efficiency_change: gpu.current.pflops_index - 100,
                        stage: 'S1', // 可从 summary API 获取
                        confidence: 'MEDIUM',
                        summary: roi.overall_verdict.description,
                    });
                }
            } catch (err) {
                console.error('Failed to fetch hero data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700">
                <div className="animate-pulse flex items-center justify-center h-24">
                    <div className="h-8 bg-slate-700 rounded w-1/2"></div>
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700">
                <p className="text-slate-400 text-center">加载失败</p>
            </div>
        );
    }

    // 判定样式
    const verdictConfig = {
        sustainable: {
            icon: CheckCircle,
            label: '可持续',
            bg: 'from-green-500/20 to-emerald-500/10',
            border: 'border-green-500/30',
            text: 'text-green-400',
            glow: 'shadow-green-500/20'
        },
        improving: {
            icon: TrendingUp,
            label: '改善中',
            bg: 'from-blue-500/20 to-cyan-500/10',
            border: 'border-blue-500/30',
            text: 'text-blue-400',
            glow: 'shadow-blue-500/20'
        },
        balanced: {
            icon: Target,
            label: '平衡',
            bg: 'from-yellow-500/20 to-amber-500/10',
            border: 'border-yellow-500/30',
            text: 'text-yellow-400',
            glow: 'shadow-yellow-500/20'
        },
        concerning: {
            icon: AlertTriangle,
            label: '需关注',
            bg: 'from-red-500/20 to-orange-500/10',
            border: 'border-red-500/30',
            text: 'text-red-400',
            glow: 'shadow-red-500/20'
        },
    };

    const config = verdictConfig[data.verdict];
    const VerdictIcon = config.icon;

    return (
        <div className={`bg-gradient-to-r ${config.bg} rounded-2xl p-8 border ${config.border} shadow-lg ${config.glow}`}>
            {/* 核心问题 */}
            <div className="text-center mb-6">
                <p className="text-slate-400 text-sm mb-2">核心问题</p>
                <h2 className="text-xl font-semibold text-white">
                    AI 投资能否实现可持续回报？
                </h2>
            </div>

            {/* 结论 */}
            <div className="flex items-center justify-center gap-3 mb-8">
                <VerdictIcon className={`w-10 h-10 ${config.text}`} />
                <span className={`text-4xl font-bold ${config.text}`}>
                    {config.label}
                </span>
            </div>

            {/* 关键指标 */}
            <div className="grid grid-cols-2 gap-6">
                {/* 覆盖率 */}
                <div className="bg-slate-800/50 rounded-xl p-4 text-center">
                    <MetricTooltip content="推理收入能否覆盖AI资产折旧成本。>100%表示收入可覆盖折旧，投资可持续。">
                        <p className="text-slate-400 text-sm mb-1">推理覆盖率</p>
                    </MetricTooltip>
                    <div className="flex items-center justify-center gap-2">
                        <span className="text-3xl font-bold text-white">
                            {(data.coverage_ratio * 100).toFixed(0)}%
                        </span>
                        <span className={`text-sm flex items-center ${data.coverage_change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {data.coverage_change > 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                            {data.coverage_change > 0 ? '+' : ''}{(data.coverage_change * 100).toFixed(0)}pp
                        </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">= 推理收入 ÷ 资产折旧</p>
                </div>

                {/* 效率指数 */}
                <div className="bg-slate-800/50 rounded-xl p-4 text-center">
                    <MetricTooltip content="每PFLOPS算力的租赁成本相对于2024Q1基准的效率提升。指数>100表示成本效率提升。">
                        <p className="text-slate-400 text-sm mb-1">算力效率指数</p>
                    </MetricTooltip>
                    <div className="flex items-center justify-center gap-2">
                        <span className="text-3xl font-bold text-white">
                            {data.efficiency_index.toFixed(0)}
                        </span>
                        <span className={`text-sm flex items-center ${data.efficiency_change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {data.efficiency_change > 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                            {data.efficiency_change > 0 ? '+' : ''}{data.efficiency_change.toFixed(0)}%
                        </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">= 2024Q1基准100</p>
                </div>
            </div>

            {/* 总结 */}
            <div className="mt-6 text-center">
                <p className="text-slate-300 text-sm">{data.summary}</p>
            </div>
        </div>
    );
}
