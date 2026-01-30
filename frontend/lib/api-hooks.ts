"use client";

import useSWR from "swr";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

// 价格数据
export interface PriceRecord {
    provider: string;
    model?: string;
    sku_id?: string;
    // API 原始字段
    price?: number;
    price_type?: "input" | "output" | "hourly";
    // 转换后的字段
    input_price?: number;
    output_price?: number;
    hourly_rate?: number;
    unit: string;
    weekOverWeek?: number | null;
    monthOverMonth?: number | null;
    yearOverYear?: number | null;
}

// 指标数据
export interface MetricData {
    id: string;
    name: string;
    value: number | string;
    unit?: string;
    status?: "good" | "warning" | "danger" | "neutral";
    trend?: number;
    weekOverWeek?: number;
    monthOverMonth?: number;
    yearOverYear?: number;
}

// 仪表盘摘要
export interface DashboardSummary {
    stage: {
        current: string;
        confidence: string;
        description: string;
    };
    key_metrics: MetricData[];
    providers: Record<string, number>;
    last_updated: string;
}

export function usePrices(provider?: string) {
    const url = provider
        ? `${API_BASE}/api/v1/data/prices/${provider}`
        : `${API_BASE}/api/v1/data/prices`;

    return useSWR<{ success: boolean; data: PriceRecord[] }>(url, fetcher, {
        refreshInterval: 60000, // 1分钟刷新
        revalidateOnFocus: false,
    });
}

export function useMetrics() {
    return useSWR<{ success: boolean; data: MetricData[] }>(
        `${API_BASE}/api/v1/data/metrics`,
        fetcher,
        {
            refreshInterval: 60000,
            revalidateOnFocus: false,
        }
    );
}

export function useSummary() {
    return useSWR<{ success: boolean; data: DashboardSummary }>(
        `${API_BASE}/api/v1/data/summary`,
        fetcher,
        {
            refreshInterval: 30000, // 30秒刷新
            revalidateOnFocus: false,
        }
    );
}

export async function refreshData(): Promise<boolean> {
    try {
        const res = await fetch(`${API_BASE}/api/v1/data/refresh`, {
            method: "POST",
        });
        const data = await res.json();
        return data.success;
    } catch {
        return false;
    }
}
