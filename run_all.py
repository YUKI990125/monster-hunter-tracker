#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《怪物猎人：旅人》渠道数据自动化采集主程序
每日运行，更新所有模块数据
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_DIR))

# 导入各模块采集器
from scrapers.nodes import collect_nodes
from scrapers.stats import collect_stats
from scrapers.activities import collect_activities
from scrapers.sentiment import collect_sentiment

def main():
    """主运行函数"""
    print(f"\n{'='*60}")
    print(f"《怪物猎人：旅人》渠道数据采集 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = {
        "run_time": datetime.now().isoformat(),
        "status": {},
        "errors": []
    }
    
    # 1. 采集节点数据
    print("📌 [1/4] 采集节点数据...")
    try:
        nodes_result = collect_nodes()
        results["status"]["nodes"] = "success"
        results["nodes"] = nodes_result
        print("   ✅ 节点数据采集完成")
    except Exception as e:
        results["status"]["nodes"] = "failed"
        results["errors"].append(f"节点采集失败: {str(e)}")
        print(f"   ❌ 节点数据采集失败: {e}")
    
    # 2. 采集统计数据
    print("\n📊 [2/4] 采集预约/下载数据...")
    try:
        stats_result = collect_stats()
        results["status"]["stats"] = "success"
        results["stats"] = stats_result
        print("   ✅ 统计数据采集完成")
    except Exception as e:
        results["status"]["stats"] = "failed"
        results["errors"].append(f"统计数据采集失败: {str(e)}")
        print(f"   ❌ 统计数据采集失败: {e}")
    
    # 3. 采集活动数据
    print("\n🎁 [3/4] 采集活动数据...")
    try:
        activities_result = collect_activities()
        results["status"]["activities"] = "success"
        results["activities"] = activities_result
        print("   ✅ 活动数据采集完成")
    except Exception as e:
        results["status"]["activities"] = "failed"
        results["errors"].append(f"活动数据采集失败: {str(e)}")
        print(f"   ❌ 活动数据采集失败: {e}")
    
    # 4. 采集舆情数据
    print("\n💬 [4/4] 采集舆情数据...")
    try:
        sentiment_result = collect_sentiment()
        results["status"]["sentiment"] = "success"
        results["sentiment"] = sentiment_result
        print("   ✅ 舆情数据采集完成")
    except Exception as e:
        results["status"]["sentiment"] = "failed"
        results["errors"].append(f"舆情数据采集失败: {str(e)}")
        print(f"   ❌ 舆情数据采集失败: {e}")
    
    # 输出汇总
    print(f"\n{'='*60}")
    print("📋 采集结果汇总:")
    success_count = sum(1 for v in results["status"].values() if v == "success")
    total_count = len(results["status"])
    print(f"   成功: {success_count}/{total_count} 模块")
    
    if results["errors"]:
        print(f"\n⚠️ 错误信息:")
        for error in results["errors"]:
            print(f"   - {error}")
    
    print(f"\n✨ 数据采集完成！")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    main()
