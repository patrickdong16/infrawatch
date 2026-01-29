/**
 * MetricCardsComponent - 指标卡片网格
 * 显示关键指标和变化率
 */

'use client';

import { formatValue, getChangeColor } from '@/lib/component-registry';
import type { DynamicComponentProps } from '@/lib/component-registry';

interface MetricCardData {
    id: string;
    label: string;
    value: number | string;
    unit?: string;
    change?: number;
    change_period?: string;
    trend?: 'up' | 'down' | 'stable';
    icon?: string;
}

interface CardsConfig {
    columns?: number;
    items?: {
        metric_id: string;
        label: string;
        format?: string;
        format_options?: Record<string, any>;
        change_rules?: {
            positive?: 'green' | 'red';
            negative?: 'red' | 'green';
        };
    }[];
}

export default function MetricCardsComponent({ config, data, isLoading, error }: DynamicComponentProps) {
    const cardsConfig = config.config as CardsConfig || {};
    const columns = cardsConfig.columns || 4;

    // Loading
    if (isLoading) {
        return (
            <div className={`grid grid-cols-2 md:grid-cols-${columns} gap-4`}>
                {[...Array(columns)].map((_, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow animate-pulse">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-3" />
                        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2" />
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16" />
                    </div>
                ))}
            </div>
        );
    }

    // Error
    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <p className="text-red-600 dark:text-red-400">加载失败</p>
            </div>
        );
    }

    const metrics = (data as MetricCardData[]) || [];

    // 空数据
    if (metrics.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
                <p className="text-gray-500">暂无指标数据</p>
            </div>
        );
    }

    return (
        <div className={`grid grid-cols-2 lg:grid-cols-${columns} gap-4`}>
            {metrics.map((metric, index) => {
                // 获取配置项
                const itemConfig = cardsConfig.items?.find(i => i.metric_id === metric.id);
                const format = itemConfig?.format || 'number';
                const changeRules = itemConfig?.change_rules;

                const formattedValue = formatValue(metric.value, format, itemConfig?.format_options);
                const changeColor = metric.change !== undefined
                    ? getChangeColor(metric.change, changeRules)
                    : '';

                return (
                    <div
                        key={metric.id || index}
                        className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100 dark:border-gray-700"
                    >
                        {/* 标签 */}
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                            {metric.label}
                        </p>

                        {/* 主值 */}
                        <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                {formattedValue}
                            </span>
                            {metric.unit && (
                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                    {metric.unit}
                                </span>
                            )}
                        </div>

                        {/* 变化率 */}
                        {metric.change !== undefined && (
                            <div className="flex items-center gap-2 mt-2">
                                <span className={`text-sm font-medium ${changeColor}`}>
                                    {metric.change > 0 ? '+' : ''}{(metric.change * 100).toFixed(1)}%
                                </span>
                                {metric.change_period && (
                                    <span className="text-xs text-gray-400">
                                        {metric.change_period}
                                    </span>
                                )}
                                {/* 趋势箭头 */}
                                <span className={changeColor}>
                                    {metric.change > 0 ? '↑' : metric.change < 0 ? '↓' : '→'}
                                </span>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
