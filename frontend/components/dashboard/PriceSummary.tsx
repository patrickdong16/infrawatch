"use client";

import Link from "next/link";
import { ChevronRight, TrendingDown, TrendingUp, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { usePrices, refreshData } from "@/lib/api-hooks";
import { useState } from "react";

function formatPrice(price: number | undefined): string {
  if (price === undefined) return "-";
  return price < 1 ? price.toFixed(3) : price.toFixed(2);
}

function TrendCell({ value }: { value?: number }) {
  if (value === undefined || value === 0) {
    return <span className="text-gray-400">-</span>;
  }

  const isDown = value < 0;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 text-sm font-medium",
        isDown ? "text-green-600" : "text-red-600"
      )}
    >
      {isDown ? (
        <TrendingDown className="w-3 h-3" />
      ) : (
        <TrendingUp className="w-3 h-3" />
      )}
      {value > 0 ? "+" : ""}{value.toFixed(1)}%
    </span>
  );
}

export function PriceSummary() {
  const { data, error, isLoading, mutate } = usePrices();
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshData();
    await mutate();
    setRefreshing(false);
  };

  // 按 provider 分组并取前几个
  const prices = data?.data?.slice(0, 8) || [];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">价格概览</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
          </button>
          <Link
            href="/prices"
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            详细价格
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Sector tabs */}
      <div className="flex gap-2 mb-4">
        <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
          B板块 - 模型API
        </span>
        <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
          C板块 - GPU租赁
        </span>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-8 text-gray-400">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" />
          加载中...
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="text-center py-8 text-red-500">
          加载失败，请检查后端 API
        </div>
      )}

      {/* Price table */}
      {!isLoading && !error && (
        <div className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-500 border-b border-gray-100">
                <th className="text-left py-2 font-medium">供应商</th>
                <th className="text-left py-2 font-medium">产品</th>
                <th className="text-right py-2 font-medium">价格</th>
                <th className="text-right py-2 font-medium">周环比</th>
                <th className="text-right py-2 font-medium">月环比</th>
                <th className="text-right py-2 font-medium">年同比</th>
              </tr>
            </thead>
            <tbody>
              {prices.map((item, index) => {
                const isGPU = item.hourly_rate !== undefined;
                const displayPrice = isGPU ? item.hourly_rate : (item.input_price || item.output_price);
                const displayUnit = isGPU ? "/hour" : "/M tokens";

                return (
                  <tr
                    key={index}
                    className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "w-1.5 h-1.5 rounded-full",
                            isGPU ? "bg-purple-500" : "bg-blue-500"
                          )}
                        />
                        <span className="text-sm font-medium text-gray-900">
                          {item.provider}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 text-sm text-gray-600">
                      {item.model || item.sku_id || "-"}
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="text-sm font-medium text-gray-900">
                        ${formatPrice(displayPrice)}
                      </span>
                      <span className="text-xs text-gray-500">{displayUnit}</span>
                    </td>
                    <td className="py-2.5 text-right">
                      <TrendCell value={item.weekOverWeek} />
                    </td>
                    <td className="py-2.5 text-right">
                      <TrendCell value={item.monthOverMonth} />
                    </td>
                    <td className="py-2.5 text-right">
                      <TrendCell value={item.yearOverYear} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && prices.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          暂无价格数据，请刷新获取
        </div>
      )}
    </div>
  );
}
