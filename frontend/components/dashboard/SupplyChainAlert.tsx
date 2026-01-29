"use client";

import Link from "next/link";
import { AlertTriangle, ChevronRight, Cpu, HardDrive } from "lucide-react";

export function SupplyChainAlert() {
  return (
    <div className="bg-gradient-to-r from-red-50 to-amber-50 rounded-xl border border-red-100 p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-red-100 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">供应链成本上行预警</h3>
            <p className="text-sm text-gray-600 mt-1">
              HBM3e 价格连续3月上涨 &gt;5%，CoWoS 产能利用率持续 98%
            </p>
            <p className="text-xs text-gray-500 mt-2">
              影响评估: 6-12月后 GPU 成本上升，C板块价格承压，M01 可能受抑制
            </p>
          </div>
        </div>
        <Link
          href="/supply-chain"
          className="flex items-center gap-1 text-sm text-red-600 hover:text-red-700 whitespace-nowrap"
        >
          查看详情
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-red-100">
        <div className="flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">HBM3e</p>
            <p className="text-sm font-semibold text-red-600">$15.5/GB ↑3.2%</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">DDR5</p>
            <p className="text-sm font-semibold text-green-600">$185 ↓2.1%</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">H100 ASP</p>
            <p className="text-sm font-semibold text-gray-700">$28,500 -</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">CoWoS利用率</p>
            <p className="text-sm font-semibold text-red-600">98% 🔴</p>
          </div>
        </div>
      </div>
    </div>
  );
}
