"use client";

import React, { useEffect, useState } from "react";
import { Cpu, TrendingDown, TrendingUp, RefreshCw, Server } from "lucide-react";

interface GPUPrice {
    gpu_type: string;
    lowest_price: number;
    provider: string;
}

interface GPUData {
    key_gpus: Record<string, GPUPrice>;
    providers: string[];
    total_prices: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function GPUPricesCard() {
    const [data, setData] = useState<GPUData | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<string>("");

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/collected/gpu-prices`);
            if (!res.ok) throw new Error("获取失败");
            const result = await res.json();
            if (result.success && result.data) {
                setData(result.data);
                setLastUpdated(result.timestamp || "");
            }
        } catch (e) {
            console.error("GPU价格获取失败:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const gpuOrder = ["H100", "H200", "A100", "B100", "B200"];

    return (
        <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                        <Cpu className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">GPU 云租赁价格</h3>
                        <p className="text-xs text-gray-500">
                            {data?.providers?.length || 0} 家云厂商最低价
                        </p>
                    </div>
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                    <RefreshCw
                        className={`w-4 h-4 text-gray-500 ${loading ? "animate-spin" : ""}`}
                    />
                </button>
            </div>

            {loading && !data ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="animate-pulse flex items-center gap-4">
                            <div className="h-10 w-20 bg-gray-200 rounded"></div>
                            <div className="flex-1 h-4 bg-gray-100 rounded"></div>
                        </div>
                    ))}
                </div>
            ) : data?.key_gpus ? (
                <div className="space-y-3">
                    {gpuOrder
                        .filter((gpu) => data.key_gpus[gpu])
                        .map((gpu) => {
                            const info = data.key_gpus[gpu];
                            return (
                                <div
                                    key={gpu}
                                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="w-16 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded flex items-center justify-center">
                                            <span className="text-white text-xs font-bold">{gpu}</span>
                                        </div>
                                        <div>
                                            <span className="text-xs text-gray-500">
                                                {info.provider}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-lg font-bold text-gray-900">
                                            ${info.lowest_price.toFixed(2)}
                                        </span>
                                        <span className="text-xs text-gray-500 ml-1">/小时</span>
                                    </div>
                                </div>
                            );
                        })}

                    {/* 厂商标签 */}
                    <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
                        {data.providers?.map((provider) => (
                            <span
                                key={provider}
                                className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                            >
                                {provider}
                            </span>
                        ))}
                    </div>

                    <p className="text-xs text-gray-400 text-center mt-2">
                        共 {data.total_prices} 个实例类型 •{" "}
                        {lastUpdated
                            ? new Date(lastUpdated).toLocaleDateString("zh-CN")
                            : "实时"}
                    </p>
                </div>
            ) : (
                <div className="text-center py-8 text-gray-500">
                    <Server className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">暂无价格数据</p>
                    <p className="text-xs text-gray-400 mt-1">运行采集器获取最新价格</p>
                </div>
            )}
        </div>
    );
}
