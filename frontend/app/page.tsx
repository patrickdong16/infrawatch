"use client";

import { useState, useEffect } from 'react';
import HeroCard from "@/components/dashboard/HeroCard";
import RevenuePanel from "@/components/dashboard/RevenuePanel";
import CostPanel from "@/components/dashboard/CostPanel";
import { SupplyChainAlert } from "@/components/dashboard/SupplyChainAlert";
import { SignalFeed } from "@/components/dashboard/SignalFeed";
import NewsFeed from "@/components/dashboard/NewsFeed";
import GPUPricesCard from "@/components/dashboard/GPUPricesCard";

export default function DashboardPage() {
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    setLastUpdated(new Date().toLocaleTimeString());
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI 投资可持续性监测</h1>
          <p className="text-gray-500 mt-1">实时追踪 AI 基建投资回报与风险</p>
        </div>
        {lastUpdated && (
          <span className="text-xs text-gray-400">
            更新于 {lastUpdated}
          </span>
        )}
      </div>

      {/* Layer 1: 核心结论 Hero */}
      <HeroCard />

      {/* Layer 2: 收入端 vs 成本端分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RevenuePanel />
        <CostPanel />
      </div>

      {/* Layer 3: 实时数据 - GPU价格 + 新闻动态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GPUPricesCard />
        <NewsFeed />
      </div>

      {/* Layer 4: 供应链风险 */}
      <SupplyChainAlert />

      {/* Layer 5: 实时动态 */}
      <SignalFeed />
    </div>
  );
}

