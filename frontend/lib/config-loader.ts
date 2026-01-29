/**
 * 配置加载器 - 前端配置获取
 * 从后端API获取配置或从静态文件加载
 */

import { cache } from 'react';

// 配置类型定义
export interface PageConfig {
  id: string;
  name: string;
  name_en?: string;
  path: string;
  icon?: string;
  sections: SectionConfig[];
}

export interface SectionConfig {
  id: string;
  type: string;
  title?: string;
  data_source?: string;
  columns?: number;
  height?: number;
  config?: Record<string, any>;
  items?: any[];
  filters?: FilterConfig[];
  pagination?: PaginationConfig;
  controls?: ControlConfig[];
}

export interface FilterConfig {
  field: string;
  type: 'select' | 'multi_select' | 'text' | 'date_range' | 'toggle';
  label?: string;
  options?: { value: string; label: string }[];
}

export interface PaginationConfig {
  page_size: number;
  show_total?: boolean;
  infinite_scroll?: boolean;
}

export interface ControlConfig {
  type: string;
  options?: any[];
  default?: any;
}

export interface NavigationConfig {
  main: NavItem[];
  footer?: NavItem[];
}

export interface NavItem {
  id: string;
  icon?: string;
  label: string;
  badge?: string;
  href?: string;
}

export interface DashboardConfig {
  pages: PageConfig[];
  navigation: NavigationConfig;
  theme?: ThemeConfig;
}

export interface ThemeConfig {
  colors: Record<string, string>;
  dark_mode?: {
    enabled: boolean;
    default: 'light' | 'dark' | 'system';
  };
}

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * 获取仪表盘配置
 * 使用React cache进行请求级缓存
 */
export const getDashboardConfig = cache(async (): Promise<DashboardConfig> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/dashboard`, {
      next: { revalidate: 300 }, // 5分钟缓存
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch config: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn('Failed to fetch config from API, using fallback', error);
    return getFallbackConfig();
  }
});

/**
 * 获取页面配置
 */
export const getPageConfig = cache(async (path: string): Promise<PageConfig | null> => {
  const config = await getDashboardConfig();
  
  // 规范化路径
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  
  const page = config.pages.find(p => p.path === normalizedPath);
  return page || null;
});

/**
 * 获取导航配置
 */
export const getNavigationConfig = cache(async (): Promise<NavigationConfig> => {
  const config = await getDashboardConfig();
  return config.navigation;
});

/**
 * 获取指标定义
 */
export async function getMetricDefinition(metricId: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/metrics/${metricId}`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * 后备配置 (当API不可用时)
 */
function getFallbackConfig(): DashboardConfig {
  return {
    pages: [
      {
        id: 'stage',
        name: '阶段仪表盘',
        path: '/stage',
        icon: 'Gauge',
        sections: [
          {
            id: 'stage_gauge',
            type: 'gauge',
            title: '当前周期阶段',
            data_source: '/api/v1/stage/current',
          },
        ],
      },
      {
        id: 'prices',
        name: '价格监测',
        path: '/prices',
        icon: 'TrendingDown',
        sections: [
          {
            id: 'current_prices',
            type: 'data_table',
            title: '当前价格',
            data_source: '/api/v1/prices/latest',
          },
        ],
      },
      {
        id: 'signals',
        name: '信号中心',
        path: '/signals',
        icon: 'Bell',
        sections: [
          {
            id: 'signal_list',
            type: 'signal_feed',
            title: '信号列表',
            data_source: '/api/v1/signals',
          },
        ],
      },
    ],
    navigation: {
      main: [
        { id: 'stage', icon: 'Gauge', label: '阶段仪表盘' },
        { id: 'prices', icon: 'TrendingDown', label: '价格监测' },
        { id: 'signals', icon: 'Bell', label: '信号中心' },
      ],
    },
  };
}

/**
 * 刷新配置缓存
 */
export async function revalidateConfig(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/v1/config/reload`, { method: 'POST' });
  } catch (error) {
    console.error('Failed to reload config', error);
  }
}
