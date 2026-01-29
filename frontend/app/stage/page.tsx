"use client";

import { useState, useEffect } from "react";
import { cn, getStageColor } from "@/lib/utils";
import { RefreshCw, TrendingUp, TrendingDown, Building2 } from "lucide-react";

interface StageData {
    stage: {
        code: string;
        name: string;
        description: string;
    };
    confidence: string;
    rationale: string;
    determined_at: string;
    key_metrics: Record<string, {
        value?: number;
        value_low?: number;
        value_high?: number;
        status: string;
        trend: string;
    }>;
    transition_risks: Record<string, {
        probability: string;
        conditions_met: number;
        conditions_total: number;
        gap?: number;
    }>;
}

interface M01Data {
    period: string;
    aggregate_low: number;
    aggregate_high: number;
    status: string;
    companies: Array<{
        company: string;
        ai_revenue: number;
        total_capex: number;
        m01_low: number;
        m01_high: number;
    }>;
}

const STAGE_INFO = {
    S0: { name: "不可持续", color: "bg-red-500", description: "基建严重过剩，收入无法覆盖折旧" },
    S1: { name: "临界过渡", color: "bg-amber-500", description: "收入快速增长但仍不足，供需紧平衡" },
    S2: { name: "早期自养", color: "bg-lime-500", description: "M01接近1.0，价格稳定" },
    S3: { name: "成熟工业化", color: "bg-green-500", description: "完全自养，价格下降但毛利稳定" },
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StagePage() {
    const [stageData, setStageData] = useState<StageData | null>(null);
    const [m01Data, setM01Data] = useState<M01Data | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [stageRes, m01Res] = await Promise.all([
                fetch(`${API_BASE}/api/v1/stage/current`),
                fetch(`${API_BASE}/api/v1/stage/m01`),
            ]);

            const stageJson = await stageRes.json();
            const m01Json = await m01Res.json();

            if (stageJson.data) setStageData(stageJson.data);
            if (m01Json.data) setM01Data(m01Json.data);
            setError(null);
        } catch (err) {
            setError("无法加载阶段数据");
            // Use fallback data
            setStageData({
                stage: { code: "S1", name: "临界过渡", description: "收入快速增长但仍不足" },
                confidence: "MEDIUM",
                rationale: "M01覆盖率在0.24-0.36区间",
                determined_at: new Date().toISOString(),
                key_metrics: {
                    M01: { value_low: 0.24, value_high: 0.36, status: "transition", trend: "improving" },
                },
                transition_risks: {
                    S2: { probability: "medium", conditions_met: 1, conditions_total: 3 },
                    S0: { probability: "low", conditions_met: 0, conditions_total: 3 },
                },
            });
            setM01Data({
                period: "2025-Q4",
                aggregate_low: 0.18,
                aggregate_high: 0.26,
                status: "transition",
                companies: [
                    { company: "MSFT", ai_revenue: 13.0, total_capex: 90.0, m01_low: 0.24, m01_high: 0.36 },
                    { company: "AMZN", ai_revenue: 8.0, total_capex: 75.0, m01_low: 0.18, m01_high: 0.27 },
                    { company: "GOOGL", ai_revenue: 6.0, total_capex: 93.0, m01_low: 0.11, m01_high: 0.16 },
                ],
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const currentStage = stageData?.stage?.code as keyof typeof STAGE_INFO || "S1";
    const stageInfo = STAGE_INFO[currentStage];

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">阶段判定</h1>
                    <p className="text-gray-500 mt-1">AI 基建可持续性周期阶段分析</p>
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                    刷新
                </button>
            </div>

            {loading && (
                <div className="flex items-center justify-center py-12 text-gray-400">
                    <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                    加载阶段数据...
                </div>
            )}

            {!loading && (
                <>
                    {/* Current Stage Card */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">当前阶段</h2>

                        {/* Stage gauge */}
                        <div className="relative mb-6">
                            <div className="h-3 rounded-full overflow-hidden bg-gradient-to-r from-red-500 via-amber-500 via-lime-500 to-green-500" />
                            <div className="flex justify-between mt-2">
                                {Object.entries(STAGE_INFO).map(([key, info]) => (
                                    <div
                                        key={key}
                                        className={cn(
                                            "text-center",
                                            key === currentStage ? "font-bold text-gray-900" : "text-gray-400"
                                        )}
                                        style={{ width: "25%" }}
                                    >
                                        <span className="text-sm">{key}</span>
                                        <br />
                                        <span className="text-xs">{info.name}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Stage info */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center gap-3 mb-2">
                                <div className={cn("w-4 h-4 rounded-full", stageInfo?.color)} />
                                <span className="text-xl font-bold text-gray-900">
                                    {currentStage} - {stageInfo?.name}
                                </span>
                                <span className={cn(
                                    "px-2 py-0.5 text-xs font-medium rounded-full",
                                    stageData?.confidence === "HIGH" ? "bg-green-100 text-green-700" :
                                        stageData?.confidence === "MEDIUM" ? "bg-amber-100 text-amber-700" :
                                            "bg-red-100 text-red-700"
                                )}>
                                    置信度: {stageData?.confidence || "MEDIUM"}
                                </span>
                            </div>
                            <p className="text-gray-600">{stageInfo?.description}</p>
                            <div className="mt-3 pt-3 border-t border-gray-200">
                                <p className="text-sm text-gray-500">
                                    <span className="font-medium">判定依据: </span>
                                    {stageData?.rationale || "M01覆盖率在0.24-0.36区间"}
                                </p>
                            </div>
                        </div>

                        {/* Transition risks */}
                        <div className="grid grid-cols-2 gap-4 mt-4">
                            <div className="bg-green-50 rounded-lg p-4 border border-green-100">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-green-700">→ S2 机会</span>
                                    <span className="text-xs text-green-600">
                                        {stageData?.transition_risks?.S2?.probability || "中"}
                                    </span>
                                </div>
                                <p className="text-xs text-green-600">
                                    满足 {stageData?.transition_risks?.S2?.conditions_met || 1}/{stageData?.transition_risks?.S2?.conditions_total || 3} 条件
                                </p>
                                <p className="text-xs text-green-500 mt-1">需 M01_low &gt; 0.7</p>
                            </div>
                            <div className="bg-red-50 rounded-lg p-4 border border-red-100">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-red-700">→ S0 风险</span>
                                    <span className="text-xs text-red-600">
                                        {stageData?.transition_risks?.S0?.probability || "低"}
                                    </span>
                                </div>
                                <p className="text-xs text-red-600">
                                    满足 {stageData?.transition_risks?.S0?.conditions_met || 0}/{stageData?.transition_risks?.S0?.conditions_total || 3} 条件
                                </p>
                                <p className="text-xs text-red-500 mt-1">A板块持续正增长中</p>
                            </div>
                        </div>
                    </div>

                    {/* M01 Analysis */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900">M01 覆盖率分析</h2>
                            <span className="text-sm text-gray-500">{m01Data?.period || "2025-Q4"}</span>
                        </div>

                        {/* Aggregate M01 */}
                        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-500">综合 M01 覆盖率区间</p>
                                    <p className="text-3xl font-bold text-gray-900">
                                        {m01Data?.aggregate_low?.toFixed(2) || "0.18"} - {m01Data?.aggregate_high?.toFixed(2) || "0.26"}
                                    </p>
                                </div>
                                <div className={cn(
                                    "px-3 py-1.5 rounded-full text-sm font-medium",
                                    m01Data?.status === "sustainable" ? "bg-green-100 text-green-700" :
                                        m01Data?.status === "healthy" ? "bg-lime-100 text-lime-700" :
                                            m01Data?.status === "transition" ? "bg-amber-100 text-amber-700" :
                                                "bg-red-100 text-red-700"
                                )}>
                                    {m01Data?.status === "sustainable" ? "可持续" :
                                        m01Data?.status === "healthy" ? "健康" :
                                            m01Data?.status === "transition" ? "过渡期" : "临界"}
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                M01 = AI推理收入 / AI相关资产年化折旧 (Capex占比 40%-60%, 折旧周期 4年)
                            </p>
                        </div>

                        {/* Company breakdown */}
                        <h3 className="text-sm font-medium text-gray-700 mb-3">龙头企业明细</h3>
                        <div className="space-y-3">
                            {m01Data?.companies?.map((company) => (
                                <div
                                    key={company.company}
                                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                                >
                                    <div className="flex items-center gap-3">
                                        <Building2 className="w-5 h-5 text-gray-400" />
                                        <div>
                                            <span className="font-medium text-gray-900">{company.company}</span>
                                            <p className="text-xs text-gray-500">
                                                AI收入 ${company.ai_revenue}B | Capex ${company.total_capex}B
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className="font-semibold text-gray-900">
                                            {company.m01_low.toFixed(2)} - {company.m01_high.toFixed(2)}
                                        </span>
                                        <div className="w-24 h-2 bg-gray-200 rounded-full mt-1 overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded-full"
                                                style={{ width: `${Math.min(100, company.m01_high * 100)}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Key Metrics */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">阶段判定指标</h2>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            {Object.entries(stageData?.key_metrics || {}).map(([key, metric]) => (
                                <div key={key} className="bg-gray-50 rounded-lg p-3">
                                    <p className="text-xs text-gray-500 mb-1">{key}</p>
                                    <p className="text-lg font-semibold text-gray-900">
                                        {metric.value_low !== undefined && metric.value_high !== undefined
                                            ? `${(metric.value_low * 100).toFixed(0)}%-${(metric.value_high * 100).toFixed(0)}%`
                                            : metric.value !== undefined
                                                ? `${metric.value}%`
                                                : "-"}
                                    </p>
                                    <div className="flex items-center gap-1 mt-1">
                                        {metric.trend === "improving" ? (
                                            <TrendingUp className="w-3 h-3 text-green-500" />
                                        ) : metric.trend === "declining" ? (
                                            <TrendingDown className="w-3 h-3 text-red-500" />
                                        ) : (
                                            <span className="w-3 h-3 bg-gray-300 rounded-full" />
                                        )}
                                        <span className="text-xs text-gray-500">{metric.status}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
