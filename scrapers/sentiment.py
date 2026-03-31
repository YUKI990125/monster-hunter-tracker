#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舆情数据采集模块
从 TapTap 评论采集舆情并分析
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

# TapTap评论页面URL
TAPTAP_REVIEW_URL = "https://www.taptap.cn/app/243984/review"

# 情感关键词
POSITIVE_KEYWORDS = [
    "期待", "画质好", "流畅", "还原", "好玩", "喜欢", "棒", "优秀",
    "不错", "推荐", "赞", "神作", "良心", "给力", "精彩", "满意"
]

NEGATIVE_KEYWORDS = [
    "垃圾", "差", "失望", "坑", "骗氪", "卡顿", "bug", "垃圾游戏",
    "难玩", "无聊", "骗钱", "差评", "恶心", "垃圾运营", "毁IP"
]

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

def analyze_sentiment(text):
    """分析文本情感"""
    text = text.lower()
    
    positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def scrape_taptap_reviews(max_reviews=100):
    """从TapTap采集评论"""
    reviews = []
    
    html = get_page_content(TAPTAP_REVIEW_URL)
    if not html:
        return reviews
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找评论元素
    review_elements = soup.find_all(['div', 'article'], class_=re.compile(r'(review|comment|评价)'))
    
    for elem in review_elements[:max_reviews]:
        # 获取评论文本
        text = elem.get_text().strip()
        
        # 尝试获取评分（如果有）
        rating = None
        rating_elem = elem.find(['span', 'div'], class_=re.compile(r'(rating|score|评分)'))
        if rating_elem:
            rating_match = re.search(r'(\d)', rating_elem.get_text())
            if rating_match:
                rating = int(rating_match.group(1))
        
        # 分析情感
        sentiment = analyze_sentiment(text)
        
        # 获取时间
        time_elem = elem.find(['time', 'span'], class_=re.compile(r'(time|date|时间)'))
        review_time = time_elem.get_text().strip() if time_elem else None
        
        review = {
            "text": text[:500],  # 限制长度
            "sentiment": sentiment,
            "rating": rating,
            "time": review_time
        }
        
        reviews.append(review)
    
    return reviews

def generate_daily_report(reviews):
    """生成每日舆情报告"""
    if not reviews:
        return None
    
    total = len(reviews)
    positive = sum(1 for r in reviews if r["sentiment"] == "positive")
    negative = sum(1 for r in reviews if r["sentiment"] == "negative")
    neutral = total - positive - negative
    
    # 提取关键词
    all_text = " ".join([r["text"] for r in reviews])
    
    positive_found = [kw for kw in POSITIVE_KEYWORDS if kw in all_text]
    negative_found = [kw for kw in NEGATIVE_KEYWORDS if kw in all_text]
    
    # 热门话题（简单提取高频词）
    hot_topics = []
    topic_patterns = [
        r'期待([^，。！？]{2,10})',
        r'希望([^，。！？]{2,10})',
        r'([\u4e00-\u9fa5]{2,4})很好',
    ]
    
    for pattern in topic_patterns:
        matches = re.findall(pattern, all_text)
        hot_topics.extend(matches[:3])
    
    # 示例评论
    positive_samples = [r["text"][:100] for r in reviews if r["sentiment"] == "positive"][:3]
    negative_samples = [r["text"][:100] for r in reviews if r["sentiment"] == "negative"][:3]
    neutral_samples = [r["text"][:100] for r in reviews if r["sentiment"] == "neutral"][:2]
    
    report = {
        "date": date.today().isoformat(),
        "summary": {
            "positive": round(positive / total * 100, 1) if total > 0 else 0,
            "neutral": round(neutral / total * 100, 1) if total > 0 else 0,
            "negative": round(negative / total * 100, 1) if total > 0 else 0,
            "total_comments": total
        },
        "hot_topics": list(set(hot_topics))[:5],
        "positive_keywords": list(set(positive_found))[:10],
        "negative_keywords": list(set(negative_found))[:10],
        "sample_comments": {
            "positive": positive_samples,
            "neutral": neutral_samples,
            "negative": negative_samples
        }
    }
    
    return report

def collect_sentiment():
    """采集舆情数据主函数"""
    # 读取现有数据
    data_file = DATA_DIR / "sentiment.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "game_name": "怪物猎人：旅人",
            "daily_reports": [],
            "history_summary": {}
        }
    
    # 采集评论
    print("   正在采集TapTap评论...")
    reviews = scrape_taptap_reviews(max_reviews=500)
    
    print(f"   📝 采集到 {len(reviews)} 条评论")
    
    # 生成今日报告
    today_report = generate_daily_report(reviews)
    
    if today_report:
        # 检查今天是否已有报告
        today = date.today().isoformat()
        existing_today = any(r.get("date") == today for r in data.get("daily_reports", []))
        
        if not existing_today:
            data.setdefault("daily_reports", []).append(today_report)
        else:
            # 更新今天的报告
            for i, r in enumerate(data["daily_reports"]):
                if r.get("date") == today:
                    data["daily_reports"][i] = today_report
                    break
        
        # 更新历史汇总
        all_reports = data.get("daily_reports", [])
        if all_reports:
            total_positive = sum(r["summary"]["positive"] for r in all_reports) / len(all_reports)
            total_neutral = sum(r["summary"]["neutral"] for r in all_reports) / len(all_reports)
            total_negative = sum(r["summary"]["negative"] for r in all_reports) / len(all_reports)
            
            # 判断趋势
            if len(all_reports) >= 2:
                recent = all_reports[-1]["summary"]["positive"]
                prev = all_reports[-2]["summary"]["positive"]
                if recent > prev + 2:
                    trend = "上升"
                elif recent < prev - 2:
                    trend = "下降"
                else:
                    trend = "稳定"
            else:
                trend = "数据不足"
            
            data["history_summary"] = {
                "total_positive": round(total_positive, 1),
                "total_neutral": round(total_neutral, 1),
                "total_negative": round(total_negative, 1),
                "trend": trend,
                "total_days": len(all_reports)
            }
    
    data["last_update"] = datetime.now().isoformat()
    
    # 保存
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 舆情数据已保存到 {data_file}")
    if today_report:
        print(f"   👍 好评率: {today_report['summary']['positive']}%")
        print(f"   😐 中立率: {today_report['summary']['neutral']}%")
        print(f"   👎 差评率: {today_report['summary']['negative']}%")
    
    return data


if __name__ == "__main__":
    result = collect_sentiment()
    
    if result.get("daily_reports"):
        latest = result["daily_reports"][-1]
        print(f"\n📋 舆情日报 - {latest['date']}")
        print(f"   总评论数: {latest['summary']['total_comments']}")
        print(f"   好评: {latest['summary']['positive']}%")
        print(f"   中立: {latest['summary']['neutral']}%")
        print(f"   差评: {latest['summary']['negative']}%")
        print(f"\n🔥 热门话题: {', '.join(latest['hot_topics'])}")
