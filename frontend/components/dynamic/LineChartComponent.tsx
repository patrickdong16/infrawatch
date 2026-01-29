/**
 * LineChartComponent - 折线图
 * 使用 Recharts 渲染时序数据
 */

'use client';

import { useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import type { DynamicComponentProps } from '@/lib/component-registry';

interface ChartConfig {
    x_axis: {
        field: string;
        type?: 'time' | 'category';
        label?: string;
    };
    y_axis: {
        field?: string;
        label?: string;
        unit?: string;
    };
    series?: {
        field: string;
        label: string;
        color?: string;
    }[];
    height?: number;
    show_legend?: boolean;
    show_grid?: boolean;
}

// 默认颜色
const defaultColors = [
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // amber
    '#EF4444', // red
    '#8B5CF6', // violet
    '#EC4899', // pink
];

export default function LineChartComponent({ config, data, isLoading, error }: DynamicComponentProps) {
    const chartConfig = config.config as ChartConfig || {};
    const height = chartConfig.height || config.height || 300;

    // 处理数据格式
    const chartData = useMemo(() => {
        if (!data || !Array.isArray(data)) return [];

        return data.map(item => ({
            ...item,
            // 格式化时间轴
            [chartConfig.x_axis?.field || 'date']:
                chartConfig.x_axis?.type === 'time'
                    ? new Date(item[chartConfig.x_axis.field]).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                    : item[chartConfig.x_axis?.field || 'date'],
        }));
    }, [data, chartConfig.x_axis]);

    // Loading
    if (isLoading) {
        return (
            <div
                className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow animate-pulse"
                style={{ height }}
            >
                <div className="h-full bg-gray-100 dark:bg-gray-700 rounded" />
            </div>
        );
    }

    // Error
    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <p className="text-red-600">图表加载失败</p>
            </div>
        );
    }

    // 空数据
    if (!chartData.length) {
        return (
            <div
                className="bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center"
                style={{ height }}
            >
                <p className="text-gray-500">暂无数据</p>
            </div>
        );
    }

    const xAxisField = chartConfig.x_axis?.field || 'date';
    const series = chartConfig.series || [
        { field: chartConfig.y_axis?.field || 'value', label: '值' }
    ];

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <ResponsiveContainer width="100%" height={height}>
                <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    {chartConfig.show_grid !== false && (
                        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    )}

                    <XAxis
                        dataKey={xAxisField}
                        tick={{ fontSize: 12 }}
                        tickLine={false}
                        axisLine={{ stroke: '#E5E7EB' }}
                    />

                    <YAxis
                        tick={{ fontSize: 12 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) =>
                            chartConfig.y_axis?.unit
                                ? `${value}${chartConfig.y_axis.unit}`
                                : value
                        }
                    />

                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            border: 'none',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                        }}
                        labelStyle={{ fontWeight: 600 }}
                    />

                    {chartConfig.show_legend !== false && (
                        <Legend
                            verticalAlign="top"
                            height={36}
                            iconType="circle"
                            iconSize={8}
                        />
                    )}

                    {series.map((s, index) => (
                        <Line
                            key={s.field}
                            type="monotone"
                            dataKey={s.field}
                            name={s.label}
                            stroke={s.color || defaultColors[index % defaultColors.length]}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4, strokeWidth: 0 }}
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
