#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动数据采集模块
从 TapTap、B站、好游快爆、4399 采集活动帖子
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
        "forum": "https://www.taptap.cn/app/243984/topic",
        "official": "https://www.taptap.cn/app/243984/topic?type=official"
    },
    "bilibili": {
        "forum": "https://space.bilibili.com/3546379674716986/dynamic"
    },
    "haoyoukuaibao": {
        "forum": "https://m.3839.com/a/148388.htm"
    },
    "4399": {
        "forum": "https://www.4399.com/pcgame/topic/51500698.html"
    }
}

# 活动关键词
REWARD_KEYWORDS = ["页面活动", "定制", "链接"]
COMMUNITY_KEYWORDS = ["有奖活动", "即可成功参与活动", "已开奖"]

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
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{1,2})月(\d{1,2})日',
    ]
    
    for pattern in patterns[:2]:
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
    
    return None

def is_reward_activity(title, content):
    """判断是否为有奖活动"""
    text = (title + " " + content).lower()
    for keyword in REWARD_KEYWORDS:
        if keyword in text:
            return True
    return False

def is_community_activity(title, content):
    """判断是否为社区活动"""
    text = (title + " " + content).lower()
    for keyword in COMMUNITY_KEYWORDS:
        if keyword in text:
            return True
    return False

def scrape_taptap_activities():
    """从TapTap采集活动"""
    activities = {"reward": [], "community": []}
    
    html = get_page_content(URLS["taptap"]["forum"])
    if not html:
        return activities
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找帖子列表
    posts = soup.find_all(['div', 'article'], class_=re.compile(r'(topic-item|post|article)'))
    
    for post in posts:
        title_elem = post.find(['h3', 'h4', 'a'], class_=re.compile(r'(title|name)'))
        title = title_elem.get_text().strip() if title_elem else ""
        content = post.get_text()
        
        link = None
        if title_elem and title_elem.name == 'a':
            link = title_elem.get('href', '')
            if link and not link.startswith('http'):
                link = 'https://www.taptap.cn' + link
        
        date = parse_date(content)
        
        activity = {
            "title": title,
            "channel": "TapTap",
            "url": link,
            "date": date,
            "content_preview": content[:200]
        }
        
        if is_reward_activity(title, content):
            activity["keywords"] = [k for k in REWARD_KEYWORDS if k in (title + content)]
            activities["reward"].append(activity)
        elif is_community_activity(title, content):
            activity["keywords"] = [k for k in COMMUNITY_KEYWORDS if k in (title + content)]
            activities["community"].append(activity)
    
    return activities

def scrape_bilibili_activities():
    """从B站采集活动"""
    activities = {"reward": [], "community": []}
    
    html = get_page_content(URLS["bilibili"]["forum"])
    if not html:
        return activities
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找动态内容
    dynamics = soup.find_all(['div', 'article'], class_=re.compile(r'(dynamic|opus|card)'))
    
    for dynamic in dynamics:
        text = dynamic.get_text()
        title = text[:100]  # B站动态通常没有标题，取前100字符
        
        link_elem = dynamic.find('a', href=True)
        link = link_elem['href'] if link_elem else None
        
        date = parse_date(text)
        
        activity = {
            "title": title,
            "channel": "B站",
            "url": link,
            "date": date,
            "content_preview": text[:200]
        }
        
        if is_reward_activity(title, text):
            activity["keywords"] = [k for k in REWARD_KEYWORDS if k in text]
            activities["reward"].append(activity)
        elif is_community_activity(title, text):
            activity["keywords"] = [k for k in COMMUNITY_KEYWORDS if k in text]
            activities["community"].append(activity)
    
    return activities

def scrape_haoyoukuaibao_activities():
    """从好游快爆采集活动"""
    activities = {"reward": [], "community": []}
    
    html = get_page_content(URLS["haoyoukuaibao"]["forum"])
    if not html:
        return activities
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    # 好游快爆页面结构不同，从整体文本提取
    # 查找活动相关内容
    sections = soup.find_all(['div', 'section', 'article'])
    
    for section in sections:
        content = section.get_text()
        title_elem = section.find(['h2', 'h3', 'h4', 'strong'])
        title = title_elem.get_text().strip() if title_elem else ""
        
        link_elem = section.find('a', href=True)
        link = link_elem['href'] if link_elem else URLS["haoyoukuaibao"]["forum"]
        
        date = parse_date(content)
        
        activity = {
            "title": title or content[:100],
            "channel": "好游快爆",
            "url": link,
            "date": date,
            "content_preview": content[:200]
        }
        
        if is_reward_activity(title, content):
            activity["keywords"] = [k for k in REWARD_KEYWORDS if k in (title + content)]
            activities["reward"].append(activity)
        elif is_community_activity(title, content):
            activity["keywords"] = [k for k in COMMUNITY_KEYWORDS if k in (title + content)]
            activities["community"].append(activity)
    
    return activities

def scrape_4399_activities():
    """从4399采集活动"""
    activities = {"reward": [], "community": []}
    
    html = get_page_content(URLS["4399"]["forum"])
    if not html:
        return activities
    
    soup = BeautifulSoup(html, 'html.parser')
    
    articles = soup.find_all(['div', 'article', 'section'])
    
    for article in articles:
        content = article.get_text()
        title_elem = article.find(['h2', 'h3', 'h4', 'a'])
        title = title_elem.get_text().strip() if title_elem else ""
        
        link = URLS["4399"]["forum"]
        if title_elem and title_elem.name == 'a':
            link = title_elem.get('href', link)
        
        date = parse_date(content)
        
        activity = {
            "title": title or content[:100],
            "channel": "4399",
            "url": link,
            "date": date,
            "content_preview": content[:200]
        }
        
        if is_reward_activity(title, content):
            activity["keywords"] = [k for k in REWARD_KEYWORDS if k in (title + content)]
            activities["reward"].append(activity)
        elif is_community_activity(title, content):
            activity["keywords"] = [k for k in COMMUNITY_KEYWORDS if k in (title + content)]
            activities["community"].append(activity)
    
    return activities

def collect_activities():
    """采集活动数据主函数"""
    # 读取现有数据
    data_file = DATA_DIR / "activities.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "game_name": "怪物猎人：旅人",
            "reward_activities": [],
            "community_activities": []
        }
    
    # 采集各渠道活动
    print("   正在采集TapTap活动...")
    taptap = scrape_taptap_activities()
    
    print("   正在采集B站活动...")
    bilibili = scrape_bilibili_activities()
    
    print("   正在采集好游快爆活动...")
    haoyoukuaibao = scrape_haoyoukuaibao_activities()
    
    print("   正在采集4399活动...")
    game_4399 = scrape_4399_activities()
    
    # 合并活动（去重）
    all_reward = []
    all_community = []
    
    seen_reward = set()
    seen_community = set()
    
    for source in [taptap, bilibili, haoyoukuaibao, game_4399]:
        for activity in source.get("reward", []):
            key = (activity.get("title", ""), activity.get("channel", ""))
            if key not in seen_reward:
                seen_reward.add(key)
                all_reward.append(activity)
        
        for activity in source.get("community", []):
            key = (activity.get("title", ""), activity.get("channel", ""))
            if key not in seen_community:
                seen_community.add(key)
                all_community.append(activity)
    
    # 添加ID
    for i, activity in enumerate(all_reward, 1):
        activity["id"] = i
    
    for i, activity in enumerate(all_community, 1):
        activity["id"] = i
    
    # 更新数据
    data["reward_activities"] = all_reward
    data["community_activities"] = all_community
    data["last_update"] = datetime.now().isoformat()
    
    # 保存
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 活动数据已保存到 {data_file}")
    print(f"   🎁 有奖活动: {len(all_reward)} 个")
    print(f"   🎮 社区活动: {len(all_community)} 个")
    
    return data


if __name__ == "__main__":
    result = collect_activities()
    print("\n📋 活动采集结果:")
    
    print("\n🎁 有奖活动:")
    for activity in result.get("reward_activities", []):
        print(f"   - [{activity['channel']}] {activity['title'][:50]}")
    
    print("\n🎮 社区活动:")
    for activity in result.get("community_activities", []):
        print(f"   - [{activity['channel']}] {activity['title'][:50]}")
