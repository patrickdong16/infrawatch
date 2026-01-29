"use client";

import Link from "next/link";
import { ChevronRight, TrendingDown, TrendingUp } from "lucide-react";
import { cn, formatPrice, formatPercent } from "@/lib/utils";

interface PriceItem {
  provider: string;
  model: string;
  price: number;
  unit: string;
  change: number;
  sector: "B" | "C";
}

const MOCK_PRICES: PriceItem[] = [
  { provider: "OpenAI", model: "GPT-4o", price: 2.5, unit: "/M tokens", change: -5.2, sector: "B" },
  { provider: "Anthropic", model: "Claude 3.5", price: 3.0, unit: "/M tokens", change: 0, sector: "B" },
  { provider: "DeepSeek", model: "V3", price: 0.14, unit: "/M tokens", change: -20, sector: "B" },
  { provider: "Lambda", model: "H100", price: 2.49, unit: "/hour", change: -2.1, sector: "C" },
  { provider: "CoreWeave", model: "H100", price: 2.85, unit: "/hour", change: 0, sector: "C" },
];

export function PriceSummary() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">价格概览</h2>
        <Link
          href="/prices"
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
        >
          详细价格
          <ChevronRight className="w-4 h-4" />
        </Link>
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

      {/* Price table */}
      <div className="overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="text-xs text-gray-500 border-b border-gray-100">
              <th className="text-left py-2 font-medium">供应商</th>
              <th className="text-left py-2 font-medium">产品</th>
              <th className="text-right py-2 font-medium">价格</th>
              <th className="text-right py-2 font-medium">周环比</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_PRICES.map((item, index) => (
              <tr
                key={index}
                className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors"
              >
                <td className="py-2.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        item.sector === "B" ? "bg-blue-500" : "bg-purple-500"
                      )}
                    />
                    <span className="text-sm font-medium text-gray-900">
                      {item.provider}
                    </span>
                  </div>
                </td>
                <td className="py-2.5 text-sm text-gray-600">{item.model}</td>
                <td className="py-2.5 text-right">
                  <span className="text-sm font-medium text-gray-900">
                    ${item.price}
                  </span>
                  <span className="text-xs text-gray-500">{item.unit}</span>
                </td>
                <td className="py-2.5 text-right">
                  <span
                    className={cn(
                      "inline-flex items-center gap-0.5 text-sm font-medium",
                      item.change < 0
                        ? "text-green-600"
                        : item.change > 0
                        ? "text-red-600"
                        : "text-gray-500"
                    )}
                  >
                    {item.change !== 0 &&
                      (item.change < 0 ? (
                        <TrendingDown className="w-3 h-3" />
                      ) : (
                        <TrendingUp className="w-3 h-3" />
                      ))}
                    {formatPercent(item.change)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
