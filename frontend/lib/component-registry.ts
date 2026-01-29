/**
 * 组件注册表 - 动态渲染核心
 * 根据配置类型映射到实际React组件
 */

import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import type { SectionConfig } from './config-loader';

// 动态导入组件 (代码分割)
const DataTableComponent = dynamic(
    () => import('@/components/dynamic/DataTableComponent'),
    { loading: () => <ComponentSkeleton /> }
);

const LineChartComponent = dynamic(
    () => import('@/components/dynamic/LineChartComponent'),
    { loading: () => <ComponentSkeleton /> }
);

const GaugeComponent = dynamic(
    () => import('@/components/dynamic/GaugeComponent'),
    { loading: () => <ComponentSkeleton /> }
);

const MetricCardsComponent = dynamic(
    () => import('@/components/dynamic/MetricCardsComponent'),
    { loading: () => <ComponentSkeleton /> }
);

const SignalFeedComponent = dynamic(
    () => import('@/components/dynamic/SignalFeedComponent'),
    { loading: () => <ComponentSkeleton /> }
);

const TimelineComponent = dynamic(
    () => import('@/components/dynamic/TimelineComponent'),
    { loading: () => <ComponentSkeleton /> }
);

// 组件属性类型
export interface DynamicComponentProps {
    config: SectionConfig;
    data?: any;
    isLoading?: boolean;
    error?: Error | null;
}

// 组件类型映射
type ComponentMap = Record<string, ComponentType<DynamicComponentProps>>;

const componentRegistry: ComponentMap = {
    data_table: DataTableComponent,
    line_chart: LineChartComponent,
    gauge: GaugeComponent,
    metric_cards: MetricCardsComponent,
    signal_feed: SignalFeedComponent,
    timeline: TimelineComponent,
};

/**
 * 获取组件
 */
export function getComponent(type: string): ComponentType<DynamicComponentProps> | null {
    return componentRegistry[type] || null;
}

/**
 * 注册自定义组件
 */
export function registerComponent(type: string, component: ComponentType<DynamicComponentProps>): void {
    componentRegistry[type] = component;
}

/**
 * 获取所有已注册的组件类型
 */
export function getRegisteredTypes(): string[] {
    return Object.keys(componentRegistry);
}

/**
 * 检查组件是否已注册
 */
export function isComponentRegistered(type: string): boolean {
    return type in componentRegistry;
}

/**
 * 组件加载骨架屏
 */
function ComponentSkeleton() {
    return (
        <div className= "animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg h-48 w-full" />
  );
}

// ============ 格式化器 ============

type Formatter = (value: any, options?: any) => string;

const formatters: Record<string, Formatter> = {
    currency: (value, options = {}) => {
        const prefix = options.prefix || '$';
        const decimals = options.decimal_places ?? 2;
        return `${prefix}${Number(value).toFixed(decimals)}`;
    },

    percent: (value, options = {}) => {
        const decimals = options.decimal_places ?? 1;
        return `${Number(value).toFixed(decimals)}%`;
    },

    percent_change: (value, options = {}) => {
        const decimals = options.decimal_places ?? 1;
        const num = Number(value) * 100; // 假设输入是小数
        const prefix = num > 0 ? '+' : '';
        return `${prefix}${num.toFixed(decimals)}%`;
    },

    number: (value, options = {}) => {
        const decimals = options.decimal_places ?? 0;
        return Number(value).toFixed(decimals);
    },

    relative_time: (value) => {
        const date = new Date(value);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        if (diffSec < 60) return '刚刚';
        if (diffMin < 60) return `${diffMin}分钟前`;
        if (diffHour < 24) return `${diffHour}小时前`;
        if (diffDay < 7) return `${diffDay}天前`;

        return date.toLocaleDateString('zh-CN');
    },

    date: (value) => {
        return new Date(value).toLocaleDateString('zh-CN');
    },

    range: (value) => {
        if (typeof value === 'object' && 'low' in value && 'high' in value) {
            return `${value.low.toFixed(2)} - ${value.high.toFixed(2)}`;
        }
        return String(value);
    },

    score: (value) => {
        return `${Math.round(Number(value))}/100`;
    },

    multiple: (value) => {
        return `${Number(value).toFixed(1)}x`;
    },

    index: (value, options = {}) => {
        const base = options.base ?? 100;
        return `${((Number(value) / base) * 100).toFixed(1)}`;
    },
};

/**
 * 格式化值
 */
export function formatValue(value: any, format: string, options?: any): string {
    if (value === null || value === undefined) {
        return '-';
    }

    const formatter = formatters[format];
    if (formatter) {
        return formatter(value, options);
    }

    return String(value);
}

/**
 * 获取嵌套对象值
 * 支持 "provider.name" 格式的路径
 */
export function getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
}

/**
 * 根据变化值获取颜色类
 */
export function getChangeColor(value: number, rules?: { positive?: string; negative?: string }): string {
    const colors = {
        positive: rules?.positive || 'green',
        negative: rules?.negative || 'red',
    };

    if (value > 0) {
        return colors.positive === 'green'
            ? 'text-green-600 dark:text-green-400'
            : 'text-red-600 dark:text-red-400';
    }
    if (value < 0) {
        return colors.negative === 'red'
            ? 'text-red-600 dark:text-red-400'
            : 'text-green-600 dark:text-green-400';
    }
    return 'text-gray-500';
}
