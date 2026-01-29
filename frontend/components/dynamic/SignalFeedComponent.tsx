/**
 * SignalFeedComponent - 信号列表
 * 实时显示触发的信号
 */

'use client';

import type { DynamicComponentProps } from '@/lib/component-registry';

interface Signal {
    id: string;
    type: string;
    severity: 'info' | 'warning' | 'critical';
    title: string;
    description: string;
    triggered_at: string;
    metric_id?: string;
    value?: number;
    threshold?: number;
}

// 严重程度样式
const severityStyles = {
    info: {
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        border: 'border-blue-200 dark:border-blue-800',
        icon: 'text-blue-500',
        badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    },
    warning: {
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-200 dark:border-yellow-800',
        icon: 'text-yellow-500',
        badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    },
    critical: {
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-200 dark:border-red-800',
        icon: 'text-red-500',
        badge: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    },
};

// 信号图标
const SignalIcon = ({ severity }: { severity: string }) => {
    const style = severityStyles[severity as keyof typeof severityStyles] || severityStyles.info;

    return (
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${style.bg}`}>
            <svg className={`w-5 h-5 ${style.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {severity === 'critical' ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                ) : severity === 'warning' ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                )}
            </svg>
        </div>
    );
};

// 相对时间
function getRelativeTime(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffMin < 1) return '刚刚';
    if (diffMin < 60) return `${diffMin}分钟前`;
    if (diffHour < 24) return `${diffHour}小时前`;
    if (diffDay < 7) return `${diffDay}天前`;

    return date.toLocaleDateString('zh-CN');
}

export default function SignalFeedComponent({ config, data, isLoading, error }: DynamicComponentProps) {
    // Loading
    if (isLoading) {
        return (
            <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4 animate-pulse">
                        <div className="flex gap-4">
                            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700" />
                            <div className="flex-1">
                                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2" />
                                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
                            </div>
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
                <p className="text-red-600 dark:text-red-400">加载失败</p>
            </div>
        );
    }

    const signals = (data as Signal[]) || [];

    // 空数据
    if (signals.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
                <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <p className="text-gray-500">暂无触发的信号</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {signals.map((signal) => {
                const style = severityStyles[signal.severity] || severityStyles.info;

                return (
                    <div
                        key={signal.id}
                        className={`${style.bg} ${style.border} border rounded-lg p-4 transition-all hover:shadow-md`}
                    >
                        <div className="flex gap-4">
                            <SignalIcon severity={signal.severity} />

                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <h3 className="font-medium text-gray-900 dark:text-white truncate">
                                        {signal.title}
                                    </h3>
                                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${style.badge}`}>
                                        {signal.severity === 'critical' ? '严重' : signal.severity === 'warning' ? '警告' : '信息'}
                                    </span>
                                </div>

                                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                                    {signal.description}
                                </p>

                                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                                    <span>{getRelativeTime(signal.triggered_at)}</span>
                                    {signal.metric_id && (
                                        <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                                            {signal.metric_id}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
