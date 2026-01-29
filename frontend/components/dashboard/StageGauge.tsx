"use client";

import { cn, getStageColor, getStagePosition } from "@/lib/utils";

interface StageGaugeProps {
  stage: "S0" | "S1" | "S2" | "S3";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  rationale: string;
}

const STAGE_INFO = {
  S0: { name: "不可持续", description: "基建严重过剩，收入无法覆盖折旧" },
  S1: { name: "临界过渡", description: "收入快速增长但仍不足，供需紧平衡" },
  S2: { name: "早期自养", description: "M01接近1.0，价格稳定" },
  S3: { name: "成熟工业化", description: "完全自养，价格下降但毛利稳定" },
};

const CONFIDENCE_LABELS = {
  HIGH: { text: "高", color: "bg-green-100 text-green-700" },
  MEDIUM: { text: "中", color: "bg-amber-100 text-amber-700" },
  LOW: { text: "低", color: "bg-red-100 text-red-700" },
};

export function StageGauge({ stage, confidence, rationale }: StageGaugeProps) {
  const stageInfo = STAGE_INFO[stage];
  const confidenceInfo = CONFIDENCE_LABELS[confidence];
  const position = getStagePosition(stage);
  const color = getStageColor(stage);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">AI 基建周期阶段</h2>
        <span className={cn("px-2.5 py-1 rounded-full text-xs font-medium", confidenceInfo.color)}>
          置信度: {confidenceInfo.text}
        </span>
      </div>

      {/* Stage gauge */}
      <div className="relative h-24 mb-8">
        {/* Gradient bar */}
        <div className="absolute bottom-0 left-0 right-0 h-4 rounded-full overflow-hidden stage-gradient" />
        
        {/* Stage markers */}
        <div className="absolute bottom-6 left-0 right-0 flex justify-between px-2">
          {Object.entries(STAGE_INFO).map(([key, info]) => {
            const isActive = key === stage;
            return (
              <div
                key={key}
                className={cn(
                  "flex flex-col items-center transition-all duration-300",
                  isActive ? "scale-110" : "opacity-60"
                )}
                style={{ width: "25%" }}
              >
                <span
                  className={cn(
                    "text-sm font-bold mb-1",
                    isActive ? "text-gray-900" : "text-gray-500"
                  )}
                >
                  {key}
                </span>
                <span className="text-xs text-gray-500 text-center">{info.name}</span>
              </div>
            );
          })}
        </div>

        {/* Current position indicator */}
        <div
          className="absolute bottom-3 transform -translate-x-1/2 transition-all duration-500"
          style={{ left: `${position}%` }}
        >
          <div
            className="w-6 h-6 rounded-full border-4 border-white shadow-lg"
            style={{ backgroundColor: color }}
          />
        </div>
      </div>

      {/* Current stage info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center gap-3 mb-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="font-semibold text-gray-900">
            {stage} - {stageInfo.name}
          </span>
        </div>
        <p className="text-sm text-gray-600">{stageInfo.description}</p>
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <span className="font-medium">判定依据: </span>
            {rationale}
          </p>
        </div>
      </div>

      {/* Transition risks */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="bg-green-50 rounded-lg p-3 border border-green-100">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-green-700">→ S2 机会</span>
            <span className="text-xs text-green-600">中</span>
          </div>
          <p className="text-xs text-green-600">需 M01_low &gt; 0.7</p>
        </div>
        <div className="bg-red-50 rounded-lg p-3 border border-red-100">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-red-700">→ S0 风险</span>
            <span className="text-xs text-red-600">低</span>
          </div>
          <p className="text-xs text-red-600">A板块持续正增长</p>
        </div>
      </div>
    </div>
  );
}
