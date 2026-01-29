/**
 * DataTableComponent - 动态数据表格
 * 支持排序、过滤、分页
 */

'use client';

import { useState, useMemo } from 'react';
import { formatValue, getNestedValue, getChangeColor } from '@/lib/component-registry';
import type { DynamicComponentProps } from '@/lib/component-registry';

interface ColumnDef {
    field: string;
    header: string;
    format?: string;
    format_options?: Record<string, any>;
    sortable?: boolean;
    width?: string;
    align?: 'left' | 'center' | 'right';
}

interface TableConfig {
    columns?: ColumnDef[];
    row_actions?: { id: string; icon: string; label: string }[];
    hover_highlight?: boolean;
    striped?: boolean;
}

export default function DataTableComponent({ config, data, isLoading, error }: DynamicComponentProps) {
    const [sortField, setSortField] = useState<string | null>(null);
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

    const tableConfig = config.config as TableConfig || {};
    const columns = tableConfig.columns || [];

    // 排序逻辑
    const sortedData = useMemo(() => {
        if (!data || !Array.isArray(data) || !sortField) return data;

        return [...data].sort((a, b) => {
            const aVal = getNestedValue(a, sortField);
            const bVal = getNestedValue(b, sortField);

            if (aVal === bVal) return 0;
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;

            const comparison = aVal < bVal ? -1 : 1;
            return sortDirection === 'asc' ? comparison : -comparison;
        });
    }, [data, sortField, sortDirection]);

    const handleSort = (field: string) => {
        if (sortField === field) {
            setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('asc');
        }
    };

    // Loading 状态
    if (isLoading) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                <div className="animate-pulse">
                    <div className="h-12 bg-gray-100 dark:bg-gray-700" />
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-14 border-t border-gray-100 dark:border-gray-700 flex items-center px-4 space-x-4">
                            <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-1/4" />
                            <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-1/4" />
                            <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-1/4" />
                            <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-1/4" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // Error 状态
    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-red-800 dark:text-red-200">加载失败: {error.message}</p>
            </div>
        );
    }

    // 空数据状态
    if (!data || !Array.isArray(data) || data.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
                <p className="text-gray-500 dark:text-gray-400">暂无数据</p>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            {columns.map((col) => (
                                <th
                                    key={col.field}
                                    scope="col"
                                    className={`
                    px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider
                    ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                    ${col.sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 select-none' : ''}
                  `}
                                    style={{ width: col.width }}
                                    onClick={() => col.sortable && handleSort(col.field)}
                                >
                                    <div className="flex items-center gap-1">
                                        {col.header}
                                        {col.sortable && sortField === col.field && (
                                            <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {sortedData.map((row: any, rowIndex: number) => (
                            <tr
                                key={row.id || rowIndex}
                                className={`
                  ${tableConfig.hover_highlight !== false ? 'hover:bg-gray-50 dark:hover:bg-gray-700/50' : ''}
                  ${tableConfig.striped && rowIndex % 2 === 1 ? 'bg-gray-50/50 dark:bg-gray-800/50' : ''}
                  transition-colors
                `}
                            >
                                {columns.map((col) => {
                                    const rawValue = getNestedValue(row, col.field);
                                    const formattedValue = col.format
                                        ? formatValue(rawValue, col.format, col.format_options)
                                        : rawValue;

                                    // 检测是否是变化率字段
                                    const isChangeField = col.format === 'percent_change';
                                    const changeColor = isChangeField ? getChangeColor(rawValue) : '';

                                    return (
                                        <td
                                            key={col.field}
                                            className={`
                        px-4 py-3 whitespace-nowrap text-sm
                        ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}
                        ${changeColor || 'text-gray-900 dark:text-gray-100'}
                      `}
                                        >
                                            {formattedValue}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
