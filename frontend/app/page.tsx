"use client";

import { StageGauge } from "@/components/dashboard/StageGauge";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { SignalFeed } from "@/components/dashboard/SignalFeed";
import { PriceSummary } from "@/components/dashboard/PriceSummary";
import { SupplyChainAlert } from "@/components/dashboard/SupplyChainAlert";

export default function DashboardPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">监测仪表盘</h1>
        <p className="text-gray-500 mt-1">AI 基建可持续性实时监测概览</p>
      </div>

      {/* Stage gauge and key metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Stage gauge - takes 2 columns */}
        <div className="lg:col-span-2">
          <StageGauge
            stage="S1"
            confidence="MEDIUM"
            rationale="M01区间 0.24-0.36，A板块指标连续两季正增长"
          />
        </div>

        {/* Key metrics */}
        <div className="space-y-4">
          <MetricCard
            title="M01 覆盖率"
            value="0.24 - 0.36"
            status="warning"
            description="过渡期"
            trend={{ value: 8, direction: "up" }}
          />
          <MetricCard
            title="B板块价格指数"
            value="$5.42"
            unit="/M tokens"
            status="good"
            trend={{ value: -8.5, direction: "down" }}
          />
          <MetricCard
            title="供应链紧张度"
            value="0.87"
            status="danger"
            description=">0.8 为紧张"
          />
        </div>
      </div>

      {/* Supply chain alert */}
      <SupplyChainAlert />

      {/* Price summary and signals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price summary */}
        <PriceSummary />

        {/* Recent signals */}
        <SignalFeed />
      </div>
    </div>
  );
}
