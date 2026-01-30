"use client";

import React, { useEffect, useState } from "react";
import {
    Newspaper,
    ExternalLink,
    TrendingUp,
    RefreshCw,
    AlertTriangle,
} from "lucide-react";

interface NewsItem {
    title: string;
    url: string;
    company: string;
    source: string;
    collected_at: string;
}

interface NewsData {
    news: NewsItem[];
    count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NewsFeed() {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<string>("");

    const fetchNews = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/collected/news-feed`);
            if (!res.ok) throw new Error("获取新闻失败");
            const data = await res.json();
            if (data.success && data.data) {
                setNews(data.data.news || []);
                setLastUpdated(data.timestamp || "");
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : "未知错误");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNews();
    }, []);

    const getCompanyColor = (company: string) => {
        const colors: Record<string, string> = {
            OPENAI: "bg-green-100 text-green-800 border-green-200",
            ANTHROPIC: "bg-orange-100 text-orange-800 border-orange-200",
            GOOGLE: "bg-blue-100 text-blue-800 border-blue-200",
            MICROSOFT: "bg-cyan-100 text-cyan-800 border-cyan-200",
            META: "bg-indigo-100 text-indigo-800 border-indigo-200",
            AMAZON: "bg-amber-100 text-amber-800 border-amber-200",
        };
        return colors[company] || "bg-gray-100 text-gray-800 border-gray-200";
    };

    return (
        <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                        <Newspaper className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">AI 领域动态</h3>
                        <p className="text-xs text-gray-500">
                            {lastUpdated
                                ? `更新于 ${new Date(lastUpdated).toLocaleString("zh-CN")}`
                                : "实时采集"}
                        </p>
                    </div>
                </div>
                <button
                    onClick={fetchNews}
                    disabled={loading}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                    <RefreshCw
                        className={`w-4 h-4 text-gray-500 ${loading ? "animate-spin" : ""}`}
                    />
                </button>
            </div>

            {error && (
                <div className="flex items-center gap-2 text-amber-600 bg-amber-50 p-3 rounded-lg mb-4">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            {loading && news.length === 0 ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="animate-pulse">
                            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                            <div className="h-3 bg-gray-100 rounded w-1/4"></div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="space-y-3">
                    {news.slice(0, 6).map((item, idx) => (
                        <a
                            key={idx}
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all group"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                    <h4 className="text-sm font-medium text-gray-900 group-hover:text-purple-600 transition-colors line-clamp-2">
                                        {item.title}
                                    </h4>
                                    <div className="flex items-center gap-2 mt-2">
                                        <span
                                            className={`px-2 py-0.5 text-xs font-medium rounded border ${getCompanyColor(
                                                item.company
                                            )}`}
                                        >
                                            {item.company}
                                        </span>
                                        <span className="text-xs text-gray-400">
                                            via {item.source}
                                        </span>
                                    </div>
                                </div>
                                <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-purple-500 flex-shrink-0 mt-1" />
                            </div>
                        </a>
                    ))}
                </div>
            )}

            {news.length === 0 && !loading && !error && (
                <div className="text-center py-8 text-gray-500">
                    <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">暂无新闻数据</p>
                    <p className="text-xs text-gray-400 mt-1">运行采集器获取最新动态</p>
                </div>
            )}
        </div>
    );
}
