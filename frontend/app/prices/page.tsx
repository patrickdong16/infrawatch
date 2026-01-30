"use client";

import { useState } from "react";
import useSWR from "swr";
import { usePrices, refreshData } from "@/lib/api-hooks";
import { cn } from "@/lib/utils";
import { RefreshCw, TrendingDown, TrendingUp, Filter, BarChart3 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fetcher for SWR
const fetcher = (url: string) => fetch(url).then(res => res.json());

// 厂商价格指数 Hook
function useProviderIndices() {
    return useSWR(`${API_BASE}/api/v1/prices/provider-indices`, fetcher, {
        refreshInterval: 60000,
    });
}

function formatPrice(price: number | undefined): string {
    if (price === undefined) return "-";
    return price < 1 ? price.toFixed(3) : price.toFixed(2);
}

function TrendCell({ value }: { value?: number | null }) {
    if (value === undefined || value === null || value === 0) {
        return <span className="text-gray-400">-</span>;
    }

    const isDown = value < 0;
    return (
        <span
            className={cn(
                "inline-flex items-center gap-0.5 text-sm font-medium",
                isDown ? "text-green-600" : "text-red-600"
            )}
        >
            {isDown ? (
                <TrendingDown className="w-3 h-3" />
            ) : (
                <TrendingUp className="w-3 h-3" />
            )}
            {value > 0 ? "+" : ""}{value.toFixed(1)}%
        </span>
    );
}

export default function PricesPage() {
    const { data, error, isLoading, mutate } = usePrices();
    const { data: indicesData } = useProviderIndices();
    const [refreshing, setRefreshing] = useState(false);
    const [sectorFilter, setSectorFilter] = useState<"all" | "B" | "C">("all");

    // 获取厂商价格指数 (只取 API 厂商)
    const providerIndices = (indicesData?.data?.indices || [])
        .filter((i: { provider: string }) => ["openai", "anthropic", "deepseek", "qwen", "minimax"].includes(i.provider))
        .slice(0, 5);
    const comparison = indicesData?.data?.comparison;

    const handleRefresh = async () => {
        setRefreshing(true);
        await refreshData();
        await mutate();
        setRefreshing(false);
    };

    // 转换 API 数据: 合并 input/output 价格为单个对象，保留趋势数据
    const rawPrices = data?.data || [];
    const prices = (() => {
        // 分组: input 和 output 需要合并，hourly 保持不变
        const grouped: Record<string, typeof rawPrices[0] & { input_price?: number; output_price?: number }> = {};

        for (const item of rawPrices) {
            const key = `${item.provider}-${item.sku_id}`;

            if (item.price_type === "input") {
                if (!grouped[key]) {
                    grouped[key] = {
                        ...item,
                        input_price: item.price,
                        // 保留趋势数据
                        weekOverWeek: item.weekOverWeek,
                        monthOverMonth: item.monthOverMonth,
                    };
                } else {
                    grouped[key].input_price = item.price;
                    // 合并时也更新趋势数据（从 input 获取）
                    grouped[key].weekOverWeek = item.weekOverWeek ?? grouped[key].weekOverWeek;
                    grouped[key].monthOverMonth = item.monthOverMonth ?? grouped[key].monthOverMonth;
                }
            } else if (item.price_type === "output") {
                if (!grouped[key]) {
                    grouped[key] = { ...item, output_price: item.price };
                } else {
                    grouped[key].output_price = item.price;
                }
            } else if (item.hourly_rate !== undefined || item.unit?.includes("hour")) {
                // GPU 租赁价格
                grouped[key] = {
                    ...item,
                    hourly_rate: item.hourly_rate || item.price,
                    weekOverWeek: item.weekOverWeek,
                    monthOverMonth: item.monthOverMonth,
                };
            } else {
                // 其他类型
                grouped[key] = item;
            }
        }

        return Object.values(grouped);
    })();

    // 重点关注的大模型厂商和代表模型 (每家2个模型)
    const FEATURED_PROVIDERS: Record<string, string[]> = {
        // B板块 - 大模型 API (每家保留2个代表模型)
        openai: ["gpt-4o", "gpt-4-turbo"],           // 去掉 O1/O3
        anthropic: ["claude-sonnet-4", "claude-opus-4.5"], // 用 opus-4.5 替代 opus-3
        qwen: ["qwen-max", "qwen-plus"],
        deepseek: ["deepseek-v3", "deepseek-r1"],
        minimax: ["abab6.5s", "abab6-chat"],
        // C板块 - 云厂商 GPU (每家保留2个代表实例)
        lambda_labs: ["h100", "a100"],
        aws: ["p5", "p4d"],
        azure: ["nd96asr", "nc24ads"],
        gcp: ["a3-highgpu", "a2-highgpu"],
    };

    // Filter by sector and featured providers
    const filteredPrices = prices.filter((item) => {
        // GPU (C板块) 不过滤
        const isGPU = item.hourly_rate !== undefined;
        if (isGPU) {
            return sectorFilter === "all" || sectorFilter === "C";
        }

        // B板块：只保留重点厂商的代表模型
        if (sectorFilter === "C") return false;

        const providerKey = item.provider?.toLowerCase();
        const modelName = (item.model || item.sku_id || "").toLowerCase();

        // 检查是否在白名单中
        for (const [provider, models] of Object.entries(FEATURED_PROVIDERS)) {
            if (providerKey?.includes(provider)) {
                // 检查是否是代表模型
                return models.some(m => modelName.includes(m.toLowerCase()));
            }
        }
        return false;
    });

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">价格监测</h1>
                    <p className="text-gray-500 mt-1">模型 API (B板块) 与 GPU 租赁 (C板块) 价格追踪</p>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
                    刷新数据
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-gray-500">
                        <Filter className="w-4 h-4" />
                        <span className="text-sm font-medium">筛选:</span>
                    </div>
                    <div className="flex gap-2">
                        {[
                            { value: "all", label: "全部" },
                            { value: "B", label: "B板块 - 模型API" },
                            { value: "C", label: "C板块 - GPU租赁" },
                        ].map((option) => (
                            <button
                                key={option.value}
                                onClick={() => setSectorFilter(option.value as "all" | "B" | "C")}
                                className={cn(
                                    "px-3 py-1.5 text-sm font-medium rounded-lg transition-colors",
                                    sectorFilter === option.value
                                        ? "bg-blue-100 text-blue-700"
                                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                                )}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* 厂商价格指数卡片 */}
            {providerIndices.length > 0 && (
                <div className="space-y-4">
                    {/* 对比横幅 */}
                    {comparison?.description && (
                        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
                            <BarChart3 className="w-5 h-5 text-amber-600" />
                            <span className="text-amber-800 font-medium">{comparison.description}</span>
                        </div>
                    )}

                    {/* 厂商卡片网格 */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                        {providerIndices.map((idx: {
                            provider: string;
                            display_name: string;
                            avg_price: number;
                            flagship_price: number;
                            budget_price: number;
                            model_count: number;
                            trend: { wow?: number; mom?: number };
                        }) => (
                            <div
                                key={idx.provider}
                                className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-semibold text-gray-900">{idx.display_name}</h4>
                                    <span className="text-xs text-gray-400">{idx.model_count} 模型</span>
                                </div>

                                {/* 平均价格 */}
                                <div className="text-2xl font-bold text-gray-900 mb-1">
                                    ${idx.avg_price.toFixed(2)}
                                    <span className="text-xs font-normal text-gray-400 ml-1">/M tokens</span>
                                </div>

                                {/* 趋势 */}
                                <div className="flex items-center gap-2 mb-3">
                                    {idx.trend?.mom != null && (
                                        <span className={cn(
                                            "text-xs font-medium px-2 py-0.5 rounded-full",
                                            idx.trend.mom < 0
                                                ? "bg-green-100 text-green-700"
                                                : "bg-red-100 text-red-700"
                                        )}>
                                            月环比 {idx.trend.mom > 0 ? "+" : ""}{idx.trend.mom.toFixed(1)}%
                                        </span>
                                    )}
                                </div>

                                {/* 价格范围 */}
                                <div className="text-xs text-gray-500 space-y-1">
                                    <div className="flex justify-between">
                                        <span>旗舰</span>
                                        <span className="font-medium">${idx.flagship_price.toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>入门</span>
                                        <span className="font-medium">${idx.budget_price.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Loading state */}
            {isLoading && (
                <div className="flex items-center justify-center py-12 text-gray-400">
                    <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                    加载价格数据...
                </div>
            )}

            {/* Error state */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                    <p className="text-red-600 font-medium">无法连接到后端 API</p>
                    <p className="text-red-500 text-sm mt-1">
                        请确保后端服务运行在 http://localhost:8000
                    </p>
                </div>
            )}

            {/* Price table */}
            {!isLoading && !error && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr className="text-xs text-gray-500 uppercase tracking-wider">
                                <th className="text-left py-3 px-4 font-medium">板块</th>
                                <th className="text-left py-3 px-4 font-medium">供应商</th>
                                <th className="text-left py-3 px-4 font-medium">产品/SKU</th>
                                <th className="text-right py-3 px-4 font-medium">当前价格</th>
                                <th className="text-right py-3 px-4 font-medium">周环比</th>
                                <th className="text-right py-3 px-4 font-medium">月环比</th>

                            </tr>
                        </thead>
                        <tbody>
                            {filteredPrices.map((item, index) => {
                                const isGPU = item.hourly_rate !== undefined;
                                const displayPrice = isGPU ? item.hourly_rate : (item.input_price || item.output_price);
                                const displayUnit = isGPU ? "/hour" : "/M tokens";

                                return (
                                    <tr
                                        key={index}
                                        className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
                                    >
                                        <td className="py-3 px-4">
                                            <span
                                                className={cn(
                                                    "px-2 py-0.5 text-xs font-medium rounded",
                                                    isGPU
                                                        ? "bg-purple-100 text-purple-700"
                                                        : "bg-blue-100 text-blue-700"
                                                )}
                                            >
                                                {isGPU ? "C" : "B"}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4">
                                            <span className="text-sm font-medium text-gray-900">
                                                {item.provider}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-sm text-gray-600">
                                            {item.model || item.sku_id || "-"}
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            {isGPU ? (
                                                <>
                                                    <span className="text-sm font-semibold text-gray-900">
                                                        ${formatPrice(item.hourly_rate)}
                                                    </span>
                                                    <span className="text-xs text-gray-500 ml-1">/hour</span>
                                                </>
                                            ) : (
                                                <div className="text-right">
                                                    <div>
                                                        <span className="text-xs text-gray-400">In: </span>
                                                        <span className="text-sm font-semibold text-gray-900">
                                                            ${formatPrice(item.input_price)}
                                                        </span>
                                                    </div>
                                                    <div>
                                                        <span className="text-xs text-gray-400">Out: </span>
                                                        <span className="text-sm font-semibold text-gray-900">
                                                            ${formatPrice(item.output_price)}
                                                        </span>
                                                    </div>
                                                    <span className="text-xs text-gray-400">/M tokens</span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            <TrendCell value={item.weekOverWeek} />
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            <TrendCell value={item.monthOverMonth} />
                                        </td>

                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>

                    {/* Empty state */}
                    {filteredPrices.length === 0 && (
                        <div className="text-center py-12 text-gray-400">
                            暂无价格数据
                        </div>
                    )}
                </div>
            )}

            {/* Summary stats */}
            {!isLoading && !error && filteredPrices.length > 0 && (
                <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                        <p className="text-xs text-gray-500 mb-1">数据条目</p>
                        <p className="text-2xl font-bold text-gray-900">{filteredPrices.length}</p>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                        <p className="text-xs text-gray-500 mb-1">B板块产品</p>
                        <p className="text-2xl font-bold text-blue-600">
                            {prices.filter((p) => !p.hourly_rate).length}
                        </p>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                        <p className="text-xs text-gray-500 mb-1">C板块产品</p>
                        <p className="text-2xl font-bold text-purple-600">
                            {prices.filter((p) => p.hourly_rate !== undefined).length}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
