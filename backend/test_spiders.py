#!/usr/bin/env python3
"""
爬虫测试脚本
测试各个爬虫的运行情况
"""

import asyncio
import json
import sys
from datetime import datetime

# 添加路径
sys.path.insert(0, '.')

from spiders import OpenAISpider, AnthropicSpider, LambdaLabsSpider


async def test_spider(spider_class, name: str):
    """测试单个爬虫"""
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print(f"{'='*50}")
    
    spider = spider_class()
    
    try:
        start = datetime.now()
        results = await spider.run()
        elapsed = (datetime.now() - start).total_seconds()
        
        print(f"✅ 成功! 耗时: {elapsed:.2f}s")
        print(f"   采集记录数: {len(results)}")
        
        if results:
            print(f"\n   示例数据 (前3条):")
            for i, item in enumerate(results[:3]):
                print(f"   {i+1}. {item.get('sku_id')}: ${item.get('price')} ({item.get('price_type', 'default')})")
        
        return {"name": name, "success": True, "count": len(results), "elapsed": elapsed, "data": results}
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return {"name": name, "success": False, "error": str(e)}


async def main():
    """运行所有爬虫测试"""
    print("="*60)
    print("InfraWatch 爬虫测试")
    print(f"时间: {datetime.now().isoformat()}")
    print("="*60)
    
    spiders = [
        (OpenAISpider, "OpenAI 定价"),
        (AnthropicSpider, "Anthropic 定价"),
        (LambdaLabsSpider, "Lambda Labs GPU云"),
    ]
    
    results = []
    for spider_class, name in spiders:
        result = await test_spider(spider_class, name)
        results.append(result)
    
    # 汇总
    print(f"\n{'='*60}")
    print("测试汇总")
    print(f"{'='*60}")
    
    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    total_records = sum(r.get("count", 0) for r in results)
    
    print(f"通过: {success}/{total}")
    print(f"总记录数: {total_records}")
    
    for r in results:
        status = "✅" if r.get("success") else "❌"
        count = r.get("count", 0)
        print(f"  {status} {r['name']}: {count} 条")
    
    # 保存结果
    output_file = "test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "success": success,
                "total_records": total_records,
            },
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {output_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
