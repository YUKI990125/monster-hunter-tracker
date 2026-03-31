#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点数据采集模块
从 TapTap、B站、好游快爆采集游戏关键节点信息
"""

import json
import re
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# 项目路径
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_DIR / "data"

# 渠道URL
URLS = {
    "taptap": {
        "game": "https://www.taptap.cn/app/243984",
        "news": "https://www.taptap.cn/app/243984/topic?type=official"
    },
    "bilibili": {
        "game": "https://gwlrlr.biligame.com/gwlryykq",
        "space": "https://space.bilibili.com/3546379674716986"
    },
    "haoyoukuaibao": {
        "game": "https://m.3839.com/a/148388.htm"
    },
    "official": {
        "main": "https://mho.qq.com/web202507/index.html",
        "news": "https://mho.qq.com/web202507/newsdetail.html"
    }
}

# 节点关键词映射
NODE_KEYWORDS = {
    "预约开启": ["预约开启", "预约现已开启", "预约正式开启"],
    "测试招募": ["测试招募", "体验团招募", "封闭测试招募", "首测招募"],
    "测试开启": ["测试开启", "首测开启", "封闭测试开启", "体验团开启"],
    "测试结束": ["测试结束", "首测结束", "封闭测试结束"],
    "公测首发定档": ["公测定档", "首发定档", "公测时间", "上线时间"],
    "前瞻直播": ["前瞻直播", "发布会直播", "定档直播"],
    "预注册": ["预注册", "预注册开启"],
    "预下载": ["预下载", "预下载开启"],
    "公测开启": ["公测开启", "正式上线", "全平台公测", "首发上线"]
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

def parse_date(text):
    """从文本中解析日期"""
    # 匹配多种日期格式
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2024年11月13日
        r'(\d{4})-(\d{1,2})-(\d{1,2})',       # 2024-11-13
        r'(\d{1,2})月(\d{1,2})日',            # 11月13日 (需要推断年份)
    ]
    
    for pattern in patterns[:2]:  # 前两种格式
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
    
    return None

def parse_time(text):
    """从文本中解析时间"""
    patterns = [
        r'(\d{1,2}):(\d{2})',  # 11:00
        r'(\d{1,2})点',        # 11点
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if len(match.groups()) > 1 else 0
            return f"{hour:02d}:{minute:02d}"
    
    return None

def scrape_taptap_nodes():
    """从TapTap采集节点信息"""
    nodes = {}
    
    # 获取官方公告页
    html = get_page_content(URLS["taptap"]["news"])
    if not html:
        return nodes
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找公告标题和内容
    articles = soup.find_all(['article', 'div'], class_=re.compile(r'(topic-item|article|post)'))
    
    for article in articles:
        text = article.get_text()
        title_elem = article.find(['h3', 'h4', 'a', 'span'], class_=re.compile(r'(title|name)'))
        title = title_elem.get_text() if title_elem else ""
        
        # 匹配节点关键词
        for node_type, keywords in NODE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title or keyword in text:
                    date = parse_date(text)
                    time = parse_time(text)
                    
                    if node_type not in nodes or (date and nodes[node_type].get("date") is None):
                        nodes[node_type] = {
                            "date": date,
                            "time": time,
                            "source": ["TapTap"],
                            "title": title,
                            "status": "已确认" if date else "待确认"
                        }
    
    return nodes

def scrape_bilibili_nodes():
    """从B站采集节点信息"""
    nodes = {}
    
    html = get_page_content(URLS["bilibili"]["space"])
    if not html:
        return nodes
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找动态内容
    dynamics = soup.find_all(['div', 'article'], class_=re.compile(r'(dynamic|opus|article)'))
    
    for dynamic in dynamics:
        text = dynamic.get_text()
        
        for node_type, keywords in NODE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    date = parse_date(text)
                    time = parse_time(text)
                    
                    if node_type not in nodes or (date and nodes[node_type].get("date") is None):
                        nodes[node_type] = {
                            "date": date,
                            "time": time,
                            "source": ["B站"],
                            "status": "已确认" if date else "待确认"
                        }
    
    return nodes

def scrape_official_nodes():
    """从官网采集节点信息"""
    nodes = {}
    
    html = get_page_content(URLS["official"]["main"])
    if not html:
        return nodes
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    # 从官网解析关键信息
    for node_type, keywords in NODE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                date = parse_date(text)
                time = parse_time(text)
                
                if node_type not in nodes or (date and nodes[node_type].get("date") is None):
                    nodes[node_type] = {
                        "date": date,
                        "time": time,
                        "source": ["官网"],
                        "status": "已确认" if date else "待确认"
                    }
    
    return nodes

def merge_nodes(*node_dicts):
    """合并多个来源的节点信息"""
    merged = {}
    
    for nodes in node_dicts:
        for node_type, info in nodes.items():
            if node_type not in merged:
                merged[node_type] = info
            else:
                # 如果有日期信息则更新
                if info.get("date") and not merged[node_type].get("date"):
                    merged[node_type]["date"] = info["date"]
                if info.get("time") and not merged[node_type].get("time"):
                    merged[node_type]["time"] = info["time"]
                # 合并来源
                if "source" in info:
                    for src in info["source"]:
                        if src not in merged[node_type].get("source", []):
                            merged[node_type].setdefault("source", []).append(src)
    
    return merged

def collect_nodes():
    """采集节点数据主函数"""
    print("   正在采集TapTap节点信息...")
    taptap_nodes = scrape_taptap_nodes()
    
    print("   正在采集B站节点信息...")
    bilibili_nodes = scrape_bilibili_nodes()
    
    print("   正在采集官网节点信息...")
    official_nodes = scrape_official_nodes()
    
    # 合并所有来源
    all_nodes = merge_nodes(taptap_nodes, bilibili_nodes, official_nodes)
    
    # 确保所有节点类型都存在
    for node_type in NODE_KEYWORDS.keys():
        if node_type not in all_nodes:
            all_nodes[node_type] = {
                "date": None,
                "time": None,
                "source": [],
                "status": "暂无" if node_type in ["前瞻直播", "预注册"] else "待定"
            }
    
    # 读取现有数据并更新
    data_file = DATA_DIR / "nodes.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {"nodes": {}}
    
    # 更新数据
    existing_data["nodes"] = all_nodes
    existing_data["last_update"] = datetime.now().isoformat()
    existing_data["game_name"] = "怪物猎人：旅人"
    
    # 保存
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 节点数据已保存到 {data_file}")
    
    return all_nodes


if __name__ == "__main__":
    result = collect_nodes()
    print("\n📋 节点采集结果:")
    for node_type, info in result.items():
        date_str = info.get("date", "待定")
        time_str = info.get("time", "")
        sources = ", ".join(info.get("source", []))
        status = info.get("status", "待定")
        print(f"   {node_type}: {date_str} {time_str} ({sources}) [{status}]")
