/**
 * TimelineComponent - 时间线组件
 * 显示历史阶段变化
 */

'use client';

import type { DynamicComponentProps } from '@/lib/component-registry';

interface TimelineEvent {
    id: string;
    date: string;
    stage: string;
    event: string;
    description?: string;
}

// 阶段颜色
const stageColors: Record<string, { bg: string; dot: string }> = {
    S0: { bg: 'bg-blue-100 dark:bg-blue-900/30', dot: 'bg-blue-500' },
    S1: { bg: 'bg-green-100 dark:bg-green-900/30', dot: 'bg-green-500' },
    S2: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', dot: 'bg-yellow-500' },
    S3: { bg: 'bg-red-100 dark:bg-red-900/30', dot: 'bg-red-500' },
};

export default function TimelineComponent({ config, data, isLoading, error }: DynamicComponentProps) {
    // Loading
    if (isLoading) {
        return (
            <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex gap-4 animate-pulse">
                        <div className="w-3 h-3 rounded-full bg-gray-300 dark:bg-gray-600 mt-1.5" />
                        <div className="flex-1">
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-2" />
                            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48" />
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    // Error
    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <p className="text-red-600">加载失败</p>
            </div>
        );
    }

    const events = (data as TimelineEvent[]) || [];

    // 空数据
    if (events.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
                <p className="text-gray-500">暂无历史记录</p>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <div className="relative">
                {/* 时间线 */}
                <div className="absolute left-1.5 top-2 bottom-2 w-0.5 bg-gray-200 dark:bg-gray-700" />

                <div className="space-y-6">
                    {events.map((event, index) => {
                        const colors = stageColors[event.stage] || { bg: 'bg-gray-100', dot: 'bg-gray-400' };

                        return (
                            <div key={event.id || index} className="relative flex gap-4">
                                {/* 圆点 */}
                                <div className={`relative z-10 w-3 h-3 rounded-full ${colors.dot} mt-1.5 ring-4 ring-white dark:ring-gray-800`} />

                                {/* 内容 */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${colors.bg} text-gray-800 dark:text-gray-200`}>
                                            {event.stage}
                                        </span>
                                        <span className="text-sm text-gray-500 dark:text-gray-400">
                                            {new Date(event.date).toLocaleDateString('zh-CN', {
                                                year: 'numeric',
                                                month: 'short',
                                                day: 'numeric',
                                            })}
                                        </span>
                                    </div>

                                    <h4 className="font-medium text-gray-900 dark:text-white">
                                        {event.event}
                                    </h4>

                                    {event.description && (
                                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                                            {event.description}
                                        </p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
