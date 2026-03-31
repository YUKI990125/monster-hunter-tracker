# 怪物猎人：旅人 - 渠道数据监控系统

## 📋 项目简介

自动化采集《怪物猎人：旅人》在各渠道的数据，生成可视化报告页面。

## 🗂️ 项目结构

```
monster-hunter-tracker/
├── data/                    # 数据存储目录
│   ├── nodes.json          # 节点数据
│   ├── stats.json          # 预约/下载数据
│   ├── activities.json     # 活动数据
│   └── sentiment.json      # 舆情数据
├── scrapers/               # 数据采集脚本
│   ├── nodes.py           # 节点采集模块
│   ├── stats.py           # 数据采集模块
│   ├── activities.py      # 活动采集模块
│   └── sentiment.py       # 舆情采集模块
├── index.html             # 一级主页
├── nodes.html             # 节点二级页面
├── stats.html             # 数据二级页面
├── activities.html        # 活动二级页面
├── sentiment.html         # 舆情二级页面
├── run_all.py             # 主运行脚本
└── README.md              # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests beautifulsoup4
```

### 2. 运行数据采集

```bash
cd monster-hunter-tracker
python run_all.py
```

### 3. 查看页面

直接用浏览器打开 `index.html` 即可查看数据可视化页面。

## 📊 四大模块说明

### 📅 节点模块
- 采集游戏关键节点时间（预约开启、测试招募、测试开启、公测定档等）
- 整合 TapTap、B站、好游快爆三个渠道信息

### 📈 数据模块
- 采集各渠道预约数、下载数
- 计算日/周/月增长率
- 支持历史数据追踪

### 🎁 活动模块
- 有奖活动：关键词"页面活动"、"定制"、"链接"
- 社区活动：关键词"有奖活动"、"即可成功参与活动"

### 💬 舆情模块
- 采集 TapTap 评论
- 自动情感分析（好评/中立/差评）
- 生成每日舆情报告

## ⏰ 自动化配置

已配置每日 10:00 自动运行采集任务。

可在 WorkBuddy 的自动化设置中查看和管理。

## 📝 数据来源

- TapTap: https://www.taptap.cn/app/243984
- B站: https://gwlrlr.biligame.com/gwlryykq
- 好游快爆: https://m.3839.com/a/148388.htm
- 4399: https://www.4399.com/pcgame/game/327065.html

## 🔧 技术栈

- Python 3.x
- requests (HTTP请求)
- BeautifulSoup (HTML解析)
- Chart.js (图表可视化)
- 纯HTML/CSS/JS前端

---

**更新时间**: 2026年3月31日
