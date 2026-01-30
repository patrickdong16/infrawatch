#!/usr/bin/env python3
"""
InfraWatch 数据采集主入口
运行所有或指定的数据采集器

用法:
    python run_collectors.py                    # 运行所有采集器
    python run_collectors.py gpu               # 只运行 GPU 价格采集
    python run_collectors.py inference         # 只运行推理覆盖率采集
    python run_collectors.py capex             # 只运行 CapEx 采集
"""

import asyncio
import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from collectors.gpu_price_collector import GPUPriceCollector
from collectors.inference_coverage_collector import InferenceCoverageCollector
from collectors.capex_collector import CapExCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_collectors")


async def run_gpu_collector() -> dict:
    """运行 GPU 价格采集器"""
    logger.info("=== 开始 GPU 价格采集 ===")
    collector = GPUPriceCollector()
    return await collector.run()


async def run_inference_collector() -> dict:
    """运行推理覆盖率采集器"""
    logger.info("=== 开始推理覆盖率采集 ===")
    collector = InferenceCoverageCollector()
    return await collector.collect_all()


async def run_capex_collector() -> dict:
    """运行 CapEx 采集器"""
    logger.info("=== 开始 CapEx 资本密集度采集 ===")
    collector = CapExCollector()
    return await collector.collect_all()


async def run_all() -> dict:
    """运行所有采集器"""
    results = {}
    
    try:
        results["gpu"] = await run_gpu_collector()
    except Exception as e:
        logger.error(f"GPU采集失败: {e}")
        results["gpu"] = {"error": str(e)}
    
    try:
        results["inference"] = await run_inference_collector()
    except Exception as e:
        logger.error(f"推理覆盖率采集失败: {e}")
        results["inference"] = {"error": str(e)}
    
    try:
        results["capex"] = await run_capex_collector()
    except Exception as e:
        logger.error(f"CapEx采集失败: {e}")
        results["capex"] = {"error": str(e)}
    
    return results


def main():
    parser = argparse.ArgumentParser(description="InfraWatch 数据采集器")
    parser.add_argument(
        "collector",
        nargs="?",
        choices=["gpu", "inference", "capex", "all"],
        default="all",
        help="要运行的采集器 (默认: all)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出结果到JSON文件",
    )
    
    args = parser.parse_args()
    
    logger.info(f"InfraWatch 数据采集 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行采集器
    if args.collector == "gpu":
        result = asyncio.run(run_gpu_collector())
    elif args.collector == "inference":
        result = asyncio.run(run_inference_collector())
    elif args.collector == "capex":
        result = asyncio.run(run_capex_collector())
    else:
        result = asyncio.run(run_all())
    
    # 输出结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"结果已保存到: {args.output}")
    else:
        print("\n=== 采集结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    logger.info("采集完成!")


if __name__ == "__main__":
    main()
