"use client";

import { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import {
    RefreshCw,
    AlertTriangle,
    TrendingUp,
    TrendingDown,
    HardDrive,
    Cpu,
    Package,
    Info,
} from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";

interface SupplyChainPrice {
    id: number;
    recorded_at: string;
    category: string;
    item: string;
    price: number;
    unit: string;
    mom_change?: number;
    yoy_change?: number;
}

interface SupplyChainIndex {
    metric_name: string;
    display_name: string;
    value: number;
    unit: string;
    changes?: { mom?: number; yoy?: number };
    description?: string;
}

interface Alert {
    type: string;
    severity: string;
    message: string;
    trigger: string;
    impact: string;
}

// 指标定义和影响说明
const METRIC_DEFINITIONS: Record<string, { definition: string; impact: string; color: string }> = {
    E_hbm_premium: {
        definition: "HBM3e单位价格 ÷ DDR5单位价格的倍数。反映高带宽内存相对传统内存的溢价水平。",
        impact: "溢价上升 → 训练/推理成本增加 → 压缩C板块利润率 → M01下降风险",
        color: "#3B82F6",
    },
    E_memory_cost_index: {
        definition: "综合HBM(权重60%)和DDR5(权重40%)价格的指数，以2024年1月为基准100。",
        impact: "指数上涨 → 基建成本上升 → 6-12月后传导至GPU租赁价格",
        color: "#10B981",
    },
    E_supply_tightness: {
        definition: "供应紧张度评分(0-1)，综合CoWoS产能利用率与HBM出货增速。>0.8为紧张。",
        impact: "紧张度高 → 交付周期延长 → GPU供应受限 → 租赁价格支撑",
        color: "#F59E0B",
    },
    E_cowos_utilization: {
        definition: "台积电CoWoS先进封装产能利用率，为AI GPU生产的关键瓶颈指标。",
        impact: ">95%时表明产能严重不足 → 新GPU供应受限 → 现有GPU租赁价格上涨",
        color: "#EF4444",
    },
};

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    HBM: <HardDrive className="w-5 h-5" />,
    DRAM: <HardDrive className="w-5 h-5" />,
    GPU: <Cpu className="w-5 h-5" />,
    Packaging: <Package className="w-5 h-5" />,
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 生成模拟12个月历史数据
function generateHistoricalData(currentValue: number, volatility: number = 0.05) {
    const data = [];
    let value = currentValue * (1 - volatility * 6); // 从较低值开始
    const now = new Date();

    for (let i = 11; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);

        // 添加随机波动，整体呈上升趋势
        const trend = (11 - i) / 11 * volatility * currentValue;
        const noise = (Math.random() - 0.5) * volatility * currentValue;
        value = Math.max(0, currentValue * (1 - volatility * 6) + trend + noise);

        data.push({
            month: date.toLocaleDateString("zh-CN", { month: "short" }),
            value: parseFloat(value.toFixed(2)),
        });
    }

    // 确保最后一个点是当前值
    data[data.length - 1].value = currentValue;
    return data;
}

export default function SupplyChainPage() {
    const [prices, setPrices] = useState<SupplyChainPrice[]>([]);
    const [indices, setIndices] = useState<SupplyChainIndex[]>([]);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedMetric, setExpandedMetric] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [pricesRes, indicesRes, alertsRes] = await Promise.all([
                fetch(`${API_BASE}/api/v1/supply-chain/latest`),
                fetch(`${API_BASE}/api/v1/supply-chain/indices`),
                fetch(`${API_BASE}/api/v1/supply-chain/alerts`),
            ]);

            const pricesJson = await pricesRes.json();
            const indicesJson = await indicesRes.json();
            const alertsJson = await alertsRes.json();

            if (pricesJson.data?.prices) setPrices(pricesJson.data.prices);
            if (indicesJson.data?.indices) setIndices(indicesJson.data.indices);
            if (alertsJson.data?.alerts) setAlerts(alertsJson.data.alerts);
        } catch {
            // Fallback data
            setPrices([
                { id: 1, recorded_at: new Date().toISOString(), category: "HBM", item: "HBM3e", price: 15.5, unit: "$/GB", mom_change: 3.2 },
                { id: 2, recorded_at: new Date().toISOString(), category: "DRAM", item: "DDR5", price: 185, unit: "$/unit", mom_change: -2.1 },
                { id: 3, recorded_at: new Date().toISOString(), category: "GPU", item: "H100 ASP", price: 28500, unit: "$/unit", mom_change: 0 },
            ]);
            setIndices([
                { metric_name: "E_hbm_premium", display_name: "HBM溢价倍数", value: 83.8, unit: "倍", changes: { mom: 2.5, yoy: 15.2 } },
                { metric_name: "E_memory_cost_index", display_name: "内存成本指数", value: 127, unit: "基准=100", changes: { mom: 1.8, yoy: 8.5 } },
                { metric_name: "E_supply_tightness", display_name: "供应链紧张度", value: 0.87, unit: "0-1", changes: { mom: 0.02 } },
                { metric_name: "E_cowos_utilization", display_name: "CoWoS产能利用率", value: 98, unit: "percent" },
            ]);
            setAlerts([
                { type: "cost_increase_warning", severity: "high", message: "HBM价格连续3月上涨>5%", trigger: "E1连续上涨 + E4>95%", impact: "C板块价格上行压力" },
                { type: "supply_tight", severity: "medium", message: "CoWoS产能利用率持续满载（98%）", trigger: "E4 > 95%", impact: "GPU供应可能受限" },
            ]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // 为每个指标生成历史数据
    const historicalData = useMemo(() => {
        const data: Record<string, { month: string; value: number }[]> = {};
        indices.forEach((index) => {
            data[index.metric_name] = generateHistoricalData(index.value, 0.08);
        });
        return data;
    }, [indices]);

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">供应链监测</h1>
                    <p className="text-gray-500 mt-1">E板块 - HBM/DRAM/GPU/封装成本追踪与预警</p>
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
                    加载供应链数据...
                </div>
            )}

            {!loading && (
                <>
                    {/* Alerts */}
                    {alerts.length > 0 && (
                        <div className="space-y-3">
                            {alerts.map((alert, index) => (
                                <div
                                    key={index}
                                    className={cn(
                                        "rounded-xl border p-4",
                                        alert.severity === "high"
                                            ? "bg-gradient-to-r from-red-50 to-amber-50 border-red-200"
                                            : "bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={cn(
                                            "p-2 rounded-lg",
                                            alert.severity === "high" ? "bg-red-100" : "bg-amber-100"
                                        )}>
                                            <AlertTriangle className={cn(
                                                "w-5 h-5",
                                                alert.severity === "high" ? "text-red-600" : "text-amber-600"
                                            )} />
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="font-semibold text-gray-900">{alert.message}</h3>
                                            <p className="text-sm text-gray-600 mt-1">
                                                <span className="font-medium">触发条件:</span> {alert.trigger}
                                            </p>
                                            <p className="text-sm text-gray-600">
                                                <span className="font-medium">影响评估:</span> {alert.impact}
                                            </p>
                                        </div>
                                        <span className={cn(
                                            "px-2 py-0.5 text-xs font-medium rounded-full",
                                            alert.severity === "high" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"
                                        )}>
                                            {alert.severity === "high" ? "高风险" : "中风险"}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Supply Chain Indices with Charts */}
                    <div className="space-y-4">
                        <h2 className="text-lg font-semibold text-gray-900">核心指标 (Rolling 12个月)</h2>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {indices.map((index) => {
                                const def = METRIC_DEFINITIONS[index.metric_name];
                                const isExpanded = expandedMetric === index.metric_name;
                                const chartData = historicalData[index.metric_name] || [];

                                return (
                                    <div
                                        key={index.metric_name}
                                        className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
                                    >
                                        {/* Header */}
                                        <div className="p-4 border-b border-gray-50">
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <p className="font-semibold text-gray-900">{index.display_name}</p>
                                                        <button
                                                            onClick={() => setExpandedMetric(isExpanded ? null : index.metric_name)}
                                                            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                                                            title="查看定义"
                                                        >
                                                            <Info className="w-4 h-4 text-gray-400" />
                                                        </button>
                                                    </div>
                                                    <div className="flex items-end gap-3 mt-1">
                                                        <p className="text-2xl font-bold text-gray-900">
                                                            {index.value}
                                                            <span className="text-sm font-normal text-gray-500 ml-1">
                                                                {index.unit === "percent" ? "%" : index.unit}
                                                            </span>
                                                        </p>
                                                        {index.changes?.mom !== undefined && (
                                                            <div className={cn(
                                                                "flex items-center gap-1 text-sm font-medium pb-0.5",
                                                                index.changes.mom > 0 ? "text-red-600" : index.changes.mom < 0 ? "text-green-600" : "text-gray-400"
                                                            )}>
                                                                {index.changes.mom > 0 ? (
                                                                    <TrendingUp className="w-4 h-4" />
                                                                ) : index.changes.mom < 0 ? (
                                                                    <TrendingDown className="w-4 h-4" />
                                                                ) : null}
                                                                月环比 {index.changes.mom > 0 ? "+" : ""}{index.changes.mom.toFixed(1)}%
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Definition Panel */}
                                            {isExpanded && def && (
                                                <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm space-y-2">
                                                    <div>
                                                        <span className="font-medium text-gray-700">定义：</span>
                                                        <span className="text-gray-600">{def.definition}</span>
                                                    </div>
                                                    <div>
                                                        <span className="font-medium text-gray-700">传导影响：</span>
                                                        <span className="text-gray-600">{def.impact}</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Chart */}
                                        <div className="p-4 pt-2">
                                            <ResponsiveContainer width="100%" height={120}>
                                                <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.5} />
                                                    <XAxis
                                                        dataKey="month"
                                                        tick={{ fontSize: 10, fill: "#9CA3AF" }}
                                                        tickLine={false}
                                                        axisLine={{ stroke: "#E5E7EB" }}
                                                    />
                                                    <YAxis
                                                        tick={{ fontSize: 10, fill: "#9CA3AF" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        domain={["dataMin - 5", "dataMax + 5"]}
                                                    />
                                                    <Tooltip
                                                        contentStyle={{
                                                            backgroundColor: "rgba(255, 255, 255, 0.95)",
                                                            border: "none",
                                                            borderRadius: "8px",
                                                            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                                                            fontSize: "12px",
                                                        }}
                                                        formatter={(value: number) => [value.toFixed(2), index.display_name]}
                                                    />
                                                    <Line
                                                        type="monotone"
                                                        dataKey="value"
                                                        stroke={def?.color || "#3B82F6"}
                                                        strokeWidth={2}
                                                        dot={false}
                                                        activeDot={{ r: 4, strokeWidth: 0 }}
                                                    />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Price Table */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100">
                            <h2 className="text-lg font-semibold text-gray-900">供应链价格明细</h2>
                        </div>
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-100">
                                <tr className="text-xs text-gray-500 uppercase tracking-wider">
                                    <th className="text-left py-3 px-4 font-medium">类别</th>
                                    <th className="text-left py-3 px-4 font-medium">项目</th>
                                    <th className="text-right py-3 px-4 font-medium">当前价格</th>
                                    <th className="text-right py-3 px-4 font-medium">月环比</th>
                                    <th className="text-right py-3 px-4 font-medium">年同比</th>
                                </tr>
                            </thead>
                            <tbody>
                                {prices.map((item) => (
                                    <tr
                                        key={item.id}
                                        className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
                                    >
                                        <td className="py-3 px-4">
                                            <div className="flex items-center gap-2">
                                                <span className="text-gray-400">
                                                    {CATEGORY_ICONS[item.category] || <Package className="w-5 h-5" />}
                                                </span>
                                                <span className="text-sm font-medium text-gray-700">{item.category}</span>
                                            </div>
                                        </td>
                                        <td className="py-3 px-4 text-sm text-gray-900 font-medium">
                                            {item.item}
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            <span className="text-sm font-semibold text-gray-900">
                                                ${item.price.toLocaleString()}
                                            </span>
                                            <span className="text-xs text-gray-500 ml-1">{item.unit.replace("$/", "/")}</span>
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            {item.mom_change !== undefined && item.mom_change !== 0 ? (
                                                <span className={cn(
                                                    "inline-flex items-center gap-0.5 text-sm font-medium",
                                                    item.mom_change > 0 ? "text-red-600" : "text-green-600"
                                                )}>
                                                    {item.mom_change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                                    {item.mom_change > 0 ? "+" : ""}{item.mom_change.toFixed(1)}%
                                                </span>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            {item.yoy_change !== undefined && item.yoy_change !== 0 ? (
                                                <span className={cn(
                                                    "inline-flex items-center gap-0.5 text-sm font-medium",
                                                    item.yoy_change > 0 ? "text-red-600" : "text-green-600"
                                                )}>
                                                    {item.yoy_change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                                    {item.yoy_change > 0 ? "+" : ""}{item.yoy_change.toFixed(1)}%
                                                </span>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {prices.length === 0 && (
                            <div className="text-center py-12 text-gray-400">
                                暂无供应链价格数据
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
