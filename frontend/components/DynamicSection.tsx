/**
 * 动态区块组件
 * 根据配置自动选择和渲染对应的组件
 */

'use client';

import useSWR from 'swr';
import { getComponent, type DynamicComponentProps } from '@/lib/component-registry';
import type { SectionConfig } from '@/lib/config-loader';

interface DynamicSectionProps {
    config: SectionConfig;
}

// API fetcher
const fetcher = (url: string) => fetch(url).then(res => res.json());

export function DynamicSection({ config }: DynamicSectionProps) {
    const Component = getComponent(config.type);

    // 如果有 data_source，使用 SWR 获取数据
    const { data, error, isLoading } = useSWR(
        config.data_source ? config.data_source : null,
        fetcher,
        {
            refreshInterval: config.type === 'signal_feed' ? 60000 : 0, // 信号列表每分钟刷新
            revalidateOnFocus: false,
        }
    );

    if (!Component) {
        return (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <p className="text-yellow-800 dark:text-yellow-200">
                    未知组件类型: <code className="font-mono">{config.type}</code>
                </p>
            </div>
        );
    }

    return (
        <section className="mb-6">
            {config.title && (
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {config.title}
                </h2>
            )}
            <Component
                config={config}
                data={data?.data ?? data}
                isLoading={isLoading}
                error={error}
            />
        </section>
    );
}

/**
 * 动态页面渲染器
 * 渲染页面的所有区块
 */
interface DynamicPageProps {
    sections: SectionConfig[];
}

export function DynamicPage({ sections }: DynamicPageProps) {
    return (
        <div className="space-y-6">
            {sections.map((section) => (
                <DynamicSection key={section.id} config={section} />
            ))}
        </div>
    );
}
