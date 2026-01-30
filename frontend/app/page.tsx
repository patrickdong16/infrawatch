"use client";

import { StageGauge } from "@/components/dashboard/StageGauge";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { SignalFeed } from "@/components/dashboard/SignalFeed";
import { PriceSummary } from "@/components/dashboard/PriceSummary";
import { SupplyChainAlert } from "@/components/dashboard/SupplyChainAlert";
import AIROICard from "@/components/dashboard/AIROICard";
import GPUEfficiencyCard from "@/components/dashboard/GPUEfficiencyCard";
import { useSummary } from "@/lib/api-hooks";
import { RefreshCw } from "lucide-react";

export default function DashboardPage() {
  const { data, isLoading, error } = useSummary();
  const summary = data?.data;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">监测仪表盘</h1>
          <p className="text-gray-500 mt-1">AI 基建可持续性实时监测概览</p>
        </div>
        {summary?.last_updated && (
          <span className="text-xs text-gray-400">
            更新于 {new Date(summary.last_updated).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" />
          加载监测数据...
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-600 font-medium">无法连接到后端 API</p>
          <p className="text-red-500 text-sm mt-1">
            请确保后端服务运行在 http://localhost:8000
          </p>
        </div>
      )}

      {/* Main content */}
      {!isLoading && !error && (
        <>
          {/* Stage gauge and key metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Stage gauge - takes 2 columns */}
            <div className="lg:col-span-2">
              <StageGauge
                stage={(summary?.stage?.current || "S1") as "S0" | "S1" | "S2" | "S3"}
                confidence={(summary?.stage?.confidence || "MEDIUM") as "HIGH" | "MEDIUM" | "LOW"}
                rationale={summary?.stage?.description || "加载中..."}
              />
            </div>

            {/* Key metrics from API */}
            <div className="space-y-4">
              {summary?.key_metrics?.map((metric, index) => (
                <MetricCard
                  key={metric.id || index}
                  title={metric.name}
                  value={metric.value}
                  unit={metric.unit}
                  status={metric.status || "neutral"}
                  weekOverWeek={metric.weekOverWeek}
                  monthOverMonth={metric.monthOverMonth}
                  yearOverYear={metric.yearOverYear}
                  showChart={true}
                />
              )) || (
                  <>
                    <MetricCard
                      title="M01 覆盖率"
                      value="0.24 - 0.36"
                      status="warning"
                      description="过渡期"
                      weekOverWeek={8}
                      showChart={true}
                    />
                    <MetricCard
                      title="B板块价格指数"
                      value="$2.73"
                      unit="/M tokens"
                      status="good"
                      weekOverWeek={-5.2}
                      monthOverMonth={-8.5}
                      showChart={true}
                    />
                    <MetricCard
                      title="C板块价格指数"
                      value="$2.49"
                      unit="/hour"
                      status="neutral"
                      weekOverWeek={-2.1}
                      monthOverMonth={-4.0}
                      showChart={true}
                    />
                  </>
                )}
            </div>
          </div>

          {/* Supply chain alert */}
          <SupplyChainAlert />

          {/* AI 投资回报分析 (核心) */}
          <AIROICard />

          {/* 成本指数 + 信号 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Price summary */}
            <PriceSummary />

            {/* GPU 算力成本效率 */}
            <GPUEfficiencyCard />

            {/* Recent signals */}
            <SignalFeed />
          </div>
        </>
      )}
    </div>
  );
}
