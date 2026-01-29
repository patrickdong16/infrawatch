/**
 * GaugeComponent - 阶段仪表盘
 * 显示当前周期阶段 (S0-S3)
 */

'use client';

import type { DynamicComponentProps } from '@/lib/component-registry';

interface StageData {
    stage: string;
    stage_name: string;
    confidence: number;
    updated_at: string;
    description?: string;
}

// 阶段颜色映射
const stageColors: Record<string, { bg: string; text: string; ring: string; gradient: string }> = {
    S0: {
        bg: 'bg-blue-100 dark:bg-blue-900/30',
        text: 'text-blue-800 dark:text-blue-200',
        ring: 'ring-blue-500',
        gradient: 'from-blue-500 to-blue-600'
    },
    S1: {
        bg: 'bg-green-100 dark:bg-green-900/30',
        text: 'text-green-800 dark:text-green-200',
        ring: 'ring-green-500',
        gradient: 'from-green-500 to-green-600'
    },
    S2: {
        bg: 'bg-yellow-100 dark:bg-yellow-900/30',
        text: 'text-yellow-800 dark:text-yellow-200',
        ring: 'ring-yellow-500',
        gradient: 'from-yellow-500 to-amber-500'
    },
    S3: {
        bg: 'bg-red-100 dark:bg-red-900/30',
        text: 'text-red-800 dark:text-red-200',
        ring: 'ring-red-500',
        gradient: 'from-red-500 to-red-600'
    },
};

// 阶段名称
const stageNames: Record<string, string> = {
    S0: '基建期',
    S1: '扩张期',
    S2: '过热期',
    S3: '收缩期',
};

export default function GaugeComponent({ config, data, isLoading, error }: DynamicComponentProps) {
    // Loading
    if (isLoading) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
                <div className="animate-pulse flex flex-col items-center">
                    <div className="w-48 h-48 rounded-full bg-gray-200 dark:bg-gray-700 mb-4" />
                    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2" />
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48" />
                </div>
            </div>
        );
    }

    // Error
    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-8 text-center">
                <p className="text-red-600 dark:text-red-400">加载失败</p>
            </div>
        );
    }

    const stageData = data as StageData;
    const stage = stageData?.stage || 'S0';
    const colors = stageColors[stage] || stageColors.S0;
    const confidence = stageData?.confidence ?? 0;

    // 计算圆环进度
    const circumference = 2 * Math.PI * 90;
    const progress = (confidence / 100) * circumference;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <div className="flex flex-col items-center">
                {/* 圆形仪表盘 */}
                <div className="relative w-52 h-52 mb-6">
                    {/* 背景圆环 */}
                    <svg className="w-full h-full transform -rotate-90">
                        <circle
                            cx="104"
                            cy="104"
                            r="90"
                            stroke="currentColor"
                            strokeWidth="12"
                            fill="none"
                            className="text-gray-200 dark:text-gray-700"
                        />
                        {/* 进度圆环 */}
                        <circle
                            cx="104"
                            cy="104"
                            r="90"
                            stroke="url(#gaugeGradient)"
                            strokeWidth="12"
                            fill="none"
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={circumference - progress}
                            className="transition-all duration-1000 ease-out"
                        />
                        <defs>
                            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" className={colors.gradient.includes('blue') ? 'stop-color: #3B82F6' : colors.gradient.includes('green') ? 'stop-color: #22C55E' : colors.gradient.includes('yellow') ? 'stop-color: #EAB308' : 'stop-color: #EF4444'} />
                                <stop offset="100%" className={colors.gradient.includes('blue') ? 'stop-color: #2563EB' : colors.gradient.includes('green') ? 'stop-color: #16A34A' : colors.gradient.includes('yellow') ? 'stop-color: #F59E0B' : 'stop-color: #DC2626'} />
                            </linearGradient>
                        </defs>
                    </svg>

                    {/* 中心内容 */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className={`text-5xl font-bold ${colors.text}`}>
                            {stage}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {stageNames[stage] || '未知阶段'}
                        </span>
                    </div>
                </div>

                {/* 置信度 */}
                <div className="text-center mb-4">
                    <span className="text-2xl font-semibold text-gray-900 dark:text-white">
                        {confidence.toFixed(0)}%
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                        置信度
                    </span>
                </div>

                {/* 描述 */}
                {stageData?.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-300 text-center max-w-sm">
                        {stageData.description}
                    </p>
                )}

                {/* 阶段指示器 */}
                <div className="flex gap-2 mt-6">
                    {['S0', 'S1', 'S2', 'S3'].map((s) => (
                        <div
                            key={s}
                            className={`
                w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium
                transition-all duration-300
                ${s === stage
                                    ? `${stageColors[s].bg} ${stageColors[s].text} ring-2 ${stageColors[s].ring} ring-offset-2 dark:ring-offset-gray-800 scale-110`
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-400'
                                }
              `}
                        >
                            {s}
                        </div>
                    ))}
                </div>

                {/* 更新时间 */}
                {stageData?.updated_at && (
                    <p className="text-xs text-gray-400 mt-4">
                        更新于: {new Date(stageData.updated_at).toLocaleString('zh-CN')}
                    </p>
                )}
            </div>
        </div>
    );
}
