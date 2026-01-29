"use client";

import { useState } from "react";
import { usePrices, refreshData } from "@/lib/api-hooks";
import { cn } from "@/lib/utils";
import { RefreshCw, TrendingDown, TrendingUp, Filter } from "lucide-react";

function formatPrice(price: number | undefined): string {
    if (price === undefined) return "-";
    return price < 1 ? price.toFixed(3) : price.toFixed(2);
}

function TrendCell({ value }: { value?: number }) {
    if (value === undefined || value === 0) {
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
    const [refreshing, setRefreshing] = useState(false);
    const [sectorFilter, setSectorFilter] = useState<"all" | "B" | "C">("all");

    const handleRefresh = async () => {
        setRefreshing(true);
        await refreshData();
        await mutate();
        setRefreshing(false);
    };

    const prices = data?.data || [];

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
                                <th className="text-right py-3 px-4 font-medium">年同比</th>
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
                                        <td className="py-3 px-4 text-right">
                                            <TrendCell value={item.yearOverYear} />
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
