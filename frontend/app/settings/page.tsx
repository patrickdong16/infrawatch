"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
    RefreshCw,
    Settings as SettingsIcon,
    Database,
    Server,
    Clock,
    CheckCircle,
    XCircle,
    Info
} from "lucide-react";
import { refreshData } from "@/lib/api-hooks";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SettingsPage() {
    const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "disconnected">("checking");
    const [refreshing, setRefreshing] = useState(false);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

    const checkApiStatus = async () => {
        setApiStatus("checking");
        try {
            const res = await fetch(`${API_BASE}/health`);
            if (res.ok) {
                setApiStatus("connected");
            } else {
                setApiStatus("disconnected");
            }
        } catch {
            setApiStatus("disconnected");
        }
    };

    const handleRefreshData = async () => {
        setRefreshing(true);
        const success = await refreshData();
        setLastRefresh(new Date());
        setRefreshing(false);
        if (success) {
            // Optionally show success notification
        }
    };

    useEffect(() => {
        checkApiStatus();
    }, []);

    return (
        <div className="space-y-6 animate-fade-in max-w-4xl">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">设置</h1>
                <p className="text-gray-500 mt-1">系统配置与连接状态</p>
            </div>

            {/* API Connection Status */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-3 mb-4">
                    <Server className="w-5 h-5 text-gray-500" />
                    <h2 className="text-lg font-semibold text-gray-900">后端 API 连接</h2>
                </div>

                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={cn(
                            "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
                            apiStatus === "connected" ? "bg-green-100 text-green-700" :
                                apiStatus === "disconnected" ? "bg-red-100 text-red-700" :
                                    "bg-gray-100 text-gray-700"
                        )}>
                            {apiStatus === "connected" ? (
                                <>
                                    <CheckCircle className="w-4 h-4" />
                                    已连接
                                </>
                            ) : apiStatus === "disconnected" ? (
                                <>
                                    <XCircle className="w-4 h-4" />
                                    未连接
                                </>
                            ) : (
                                <>
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                    检测中...
                                </>
                            )}
                        </div>
                        <span className="text-sm text-gray-500">
                            {API_BASE}
                        </span>
                    </div>
                    <button
                        onClick={checkApiStatus}
                        className="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                        重新检测
                    </button>
                </div>

                {apiStatus === "disconnected" && (
                    <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-100">
                        <p className="text-sm text-red-600">
                            无法连接到后端 API。请确保后端服务已启动：
                        </p>
                        <code className="block mt-2 text-xs bg-red-100 p-2 rounded">
                            cd backend && python3 run_mvp.py
                        </code>
                    </div>
                )}
            </div>

            {/* Data Refresh */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-3 mb-4">
                    <Database className="w-5 h-5 text-gray-500" />
                    <h2 className="text-lg font-semibold text-gray-900">数据管理</h2>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                            <p className="font-medium text-gray-900">手动刷新数据</p>
                            <p className="text-sm text-gray-500">触发后端爬虫重新获取最新价格数据</p>
                        </div>
                        <button
                            onClick={handleRefreshData}
                            disabled={refreshing || apiStatus !== "connected"}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
                            {refreshing ? "刷新中..." : "刷新数据"}
                        </button>
                    </div>

                    {lastRefresh && (
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Clock className="w-4 h-4" />
                            上次刷新: {lastRefresh.toLocaleTimeString()}
                        </div>
                    )}
                </div>
            </div>

            {/* System Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-3 mb-4">
                    <Info className="w-5 h-5 text-gray-500" />
                    <h2 className="text-lg font-semibold text-gray-900">系统信息</h2>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">应用版本</p>
                        <p className="text-sm font-medium text-gray-900">InfraWatch MVP v0.1.0</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">前端框架</p>
                        <p className="text-sm font-medium text-gray-900">Next.js 14.1.0</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">后端框架</p>
                        <p className="text-sm font-medium text-gray-900">FastAPI 0.110+</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">数据刷新间隔</p>
                        <p className="text-sm font-medium text-gray-900">30 秒 (自动)</p>
                    </div>
                </div>
            </div>

            {/* Documentation Links */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-3 mb-4">
                    <SettingsIcon className="w-5 h-5 text-gray-500" />
                    <h2 className="text-lg font-semibold text-gray-900">文档与资源</h2>
                </div>

                <div className="space-y-2">
                    <a
                        href={`${API_BASE}/docs`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                        <p className="font-medium text-blue-600">API 文档 (Swagger UI)</p>
                        <p className="text-sm text-gray-500">{API_BASE}/docs</p>
                    </a>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="font-medium text-gray-900">项目文档</p>
                        <p className="text-sm text-gray-500">请参阅项目根目录的 REQUIREMENTS.md 和 CLAUDE.md</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
