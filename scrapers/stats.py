#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计数据采集模块
从 TapTap、B站、好游快爆、4399 采集预约/下载数据
"""

import json
import re
from datetime import datetime, date
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# 项目路径
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_DIR / "data"

# 渠道URL
URLS = {
    "taptap": "https://www.taptap.cn/app/243984",
    "bilibili": "https://www.bilibili.com/video/BV1y9ZjBYEoe",  # B站官方视频页面，显示预约数
    "bilibili_game": "https://www.biligame.com/detail/?id=113695",  # B站游戏中心
    "haoyoukuaibao": "https://m.3839.com/a/148388.htm",
    "4399": "https://www.4399.com/pcgame/game/327065.html"
}

def get_page_content(url, timeout=10):
    """获取页面内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"   ⚠️ 获取页面失败 {url}: {e}")
        return None

def parse_number(text):
    """解析数字（支持万、亿单位）"""
    text = text.strip()
    
    # 处理带单位的数字
    match = re.search(r'([\d.]+)\s*万', text)
    if match:
        return int(float(match.group(1)) * 10000)
    
    match = re.search(r'([\d.]+)\s*亿', text)
    if match:
        return int(float(match.group(1)) * 100000000)
    
    # 纯数字
    match = re.search(r'[\d,]+', text)
    if match:
        return int(match.group().replace(',', ''))
    
    return 0

def scrape_taptap_stats():
    """从TapTap采集预约数"""
    stats = {"reserve": 0, "download": 0}
    
    html = get_page_content(URLS["taptap"])
    if not html:
        return stats
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找预约数 - 多种可能的CSS选择器
    reserve_patterns = [
        ('span', re.compile(r'(reserve|booking|预约)')),
        ('div', re.compile(r'(app-info|stat)')),
        ('strong', None),
    ]
    
    for tag, class_pattern in reserve_patterns:
        elements = soup.find_all(tag, class_=class_pattern) if class_pattern else soup.find_all(tag)
        for elem in elements:
            text = elem.get_text()
            if '预约' in text or '万' in text:
                # 尝试提取数字
                nums = re.findall(r'[\d.]+万?|\d+', text)
                for num in nums:
                    val = parse_number(num)
                    if val > 100000:  # 预约数通常大于10万
                        stats["reserve"] = val
                        return stats
    
    # 备用方案：从页面文本中搜索
    text = soup.get_text()
    match = re.search(r'预约.*?(\d+\.?\d*\s*万?)', text)
    if match:
        stats["reserve"] = parse_number(match.group(1))
    
    return stats

def scrape_bilibili_stats():
    """从B站采集预约数 - 从视频页面获取"""
    stats = {"reserve": 0, "download": 0, "note": "B站游戏中心预约数"}
    
    # 尝试从B站视频页面获取预约数
    html = get_page_content(URLS["bilibili"])
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # 查找"XX万人已预约"格式
        match = re.search(r'(\d+\.?\d*)\s*万?\s*人已预约', text)
        if match:
            stats["reserve"] = parse_number(match.group(1))
            return stats
    
    # 备用：尝试B站游戏中心页面
    html = get_page_content(URLS.get("bilibili_game", ""))
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        match = re.search(r'(\d+\.?\d*)\s*万?\s*人已预约', text)
        if match:
            stats["reserve"] = parse_number(match.group(1))
            return stats
    
    return stats

def scrape_haoyoukuaibao_stats():
    """从好游快爆采集预约数"""
    stats = {"reserve": 0, "download": 0}
    
    html = get_page_content(URLS["haoyoukuaibao"])
    if not html:
        return stats
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    # 查找预约数
    match = re.search(r'(\d+\.?\d*)\s*万?\s*预约', text)
    if match:
        stats["reserve"] = parse_number(match.group(1))
    else:
        # 备用方案
        match = re.search(r'预约人数.*?(\d+\.?\d*\s*万?)', text)
        if match:
            stats["reserve"] = parse_number(match.group(1))
    
    return stats

def scrape_4399_stats():
    """从4399采集预约数"""
    stats = {"reserve": 0, "download": 0, "note": "4399暂无预约数据入口"}
    
    html = get_page_content(URLS["4399"])
    if not html:
        return stats
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    # 4399可能有关注数
    match = re.search(r'(\d+\.?\d*)\s*人?\s*(关注|预约)', text)
    if match:
        stats["reserve"] = parse_number(match.group(1))
    
    return stats

def calculate_growth_rates(history):
    """计算增长率"""
    if len(history) < 2:
        return {"daily": 0, "weekly": 0, "monthly": 0}
    
    latest = history[-1]
    total_latest = latest.get("total_reserve", 0)
    
    # 日增长
    daily_growth = 0
    if len(history) >= 2:
        prev = history[-2]
        total_prev = prev.get("total_reserve", 0)
        if total_prev > 0:
            daily_growth = round((total_latest - total_prev) / total_prev * 100, 2)
    
    # 周增长
    weekly_growth = 0
    if len(history) >= 7:
        week_ago = history[-7]
        total_week = week_ago.get("total_reserve", 0)
        if total_week > 0:
            weekly_growth = round((total_latest - total_week) / total_week * 100, 2)
    
    # 月增长
    monthly_growth = 0
    if len(history) >= 30:
        month_ago = history[-30]
        total_month = month_ago.get("total_reserve", 0)
        if total_month > 0:
            monthly_growth = round((total_latest - total_month) / total_month * 100, 2)
    
    return {
        "daily": daily_growth,
        "weekly": weekly_growth,
        "monthly": monthly_growth
    }

def validate_reserve_data(new_value, old_value, tolerance=0.05):
    """
    验证预约数据的合理性
    预约数是累计值，不应该下降（除非在容差范围内，可能是精度问题）
    
    Args:
        new_value: 新采集的值
        old_value: 上次的值
        tolerance: 容差比例，默认5%（考虑精度误差）
    
    Returns:
        (validated_value, is_valid): 验证后的值和是否有效
    """
    if old_value == 0:
        return new_value, True
    
    # 计算变化比例
    change_ratio = (new_value - old_value) / old_value
    
    # 如果新值大于旧值，正常增长
    if new_value >= old_value:
        return new_value, True
    
    # 如果下降幅度在容差范围内（可能是精度问题），保留旧值
    if abs(change_ratio) <= tolerance:
        print(f"      ⚠️ 检测到小幅下降 ({change_ratio*100:.2f}%)，可能是精度问题，保留旧值")
        return old_value, False
    
    # 下降幅度过大，保留旧值并警告
    print(f"      ⚠️ 检测到异常下降 ({change_ratio*100:.2f}%)，保留旧值，请人工确认")
    return old_value, False

def collect_stats():
    """采集统计数据主函数"""
    # 读取现有数据
    data_file = DATA_DIR / "stats.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "game_name": "怪物猎人：旅人",
            "current": {},
            "history": [],
            "growth_rate": {}
        }
    
    # 获取旧数据用于验证
    old_data = data.get("current", {})
    old_taptap = old_data.get("taptap", {}).get("reserve", 0)
    old_bilibili = old_data.get("bilibili", {}).get("reserve", 0)
    old_haoyoukuaibao = old_data.get("haoyoukuaibao", {}).get("reserve", 0)
    old_4399 = old_data.get("4399", {}).get("reserve", 0)
    
    # 采集各渠道数据
    print("   正在采集TapTap数据...")
    taptap = scrape_taptap_stats()
    taptap["reserve"], _ = validate_reserve_data(taptap["reserve"], old_taptap)
    
    print("   正在采集B站数据...")
    bilibili = scrape_bilibili_stats()
    bilibili["reserve"], _ = validate_reserve_data(bilibili["reserve"], old_bilibili)
    
    print("   正在采集好游快爆数据...")
    haoyoukuaibao = scrape_haoyoukuaibao_stats()
    haoyoukuaibao["reserve"], _ = validate_reserve_data(haoyoukuaibao["reserve"], old_haoyoukuaibao)
    
    print("   正在采集4399数据...")
    game_4399 = scrape_4399_stats()
    game_4399["reserve"], _ = validate_reserve_data(game_4399["reserve"], old_4399)
    
    now = datetime.now()
    
    # 更新当前数据
    data["current"] = {
        "taptap": {
            "reserve": taptap["reserve"],
            "download": taptap["download"],
            "update_time": now.isoformat()
        },
        "bilibili": {
            "reserve": bilibili["reserve"],
            "download": bilibili["download"],
            "update_time": now.isoformat(),
            "note": bilibili.get("note", "")
        },
        "haoyoukuaibao": {
            "reserve": haoyoukuaibao["reserve"],
            "download": haoyoukuaibao["download"],
            "update_time": now.isoformat()
        },
        "4399": {
            "reserve": game_4399["reserve"],
            "download": game_4399["download"],
            "update_time": now.isoformat(),
            "note": game_4399.get("note", "")
        }
    }
    
    # 计算总预约数
    total_reserve = (
        taptap["reserve"] + 
        bilibili["reserve"] + 
        haoyoukuaibao["reserve"] + 
        game_4399["reserve"]
    )
    
    # 添加历史记录（每天只记录一次）
    today = date.today().isoformat()
    existing_today = any(h.get("date") == today for h in data.get("history", []))
    
    if not existing_today:
        data.setdefault("history", []).append({
            "date": today,
            "taptap_reserve": taptap["reserve"],
            "bilibili_reserve": bilibili["reserve"],
            "haoyoukuaibao_reserve": haoyoukuaibao["reserve"],
            "reserve_4399": game_4399["reserve"],
            "total_reserve": total_reserve
        })
    else:
        # 更新今天的数据
        for h in data["history"]:
            if h.get("date") == today:
                h.update({
                    "taptap_reserve": taptap["reserve"],
                    "bilibili_reserve": bilibili["reserve"],
                    "haoyoukuaibao_reserve": haoyoukuaibao["reserve"],
                    "reserve_4399": game_4399["reserve"],
                    "total_reserve": total_reserve
                })
                break
    
    # 计算增长率
    data["growth_rate"] = calculate_growth_rates(data.get("history", []))
    data["last_update"] = now.isoformat()
    
    # 保存
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 统计数据已保存到 {data_file}")
    print(f"   📊 总预约数: {total_reserve:,}")
    
    return data


if __name__ == "__main__":
    result = collect_stats()
    print("\n📋 统计采集结果:")
    for channel, info in result["current"].items():
        reserve = info.get("reserve", 0)
        print(f"   {channel}: {reserve:,} 预约")
    
    print(f"\n📈 增长率:")
    for period, rate in result["growth_rate"].items():
        print(f"   {period}: {rate}%")
