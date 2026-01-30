"use client";

import HeroCard from "@/components/dashboard/HeroCard";
import RevenuePanel from "@/components/dashboard/RevenuePanel";
import CostPanel from "@/components/dashboard/CostPanel";
import { SupplyChainAlert } from "@/components/dashboard/SupplyChainAlert";
import { SignalFeed } from "@/components/dashboard/SignalFeed";
import { RefreshCw } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI 投资可持续性监测</h1>
          <p className="text-gray-500 mt-1">实时追踪 AI 基建投资回报与风险</p>
        </div>
        <span className="text-xs text-gray-400">
          更新于 {new Date().toLocaleTimeString()}
        </span>
      </div>

      {/* Layer 1: 核心结论 Hero */}
      <HeroCard />

      {/* Layer 2: 收入端 vs 成本端分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RevenuePanel />
        <CostPanel />
      </div>

      {/* Layer 3: 供应链风险 */}
      <SupplyChainAlert />

      {/* Layer 4: 实时动态 */}
      <SignalFeed />
    </div>
  );
}
