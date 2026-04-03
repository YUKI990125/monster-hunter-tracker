# 怪物猎人：旅人 - 渠道数据监控

## 📁 项目结构

```
monster-hunter-tracker/
├── share.html          # 📌 分享页面（单文件，可直接发送给别人）
├── index.html          # 主监控平台入口
├── stats.html          # 数据统计详情
├── nodes.html          # 节点追踪
├── activities.html     # 活动追踪
├── sentiment.html      # 舆情分析
├── data/               # JSON数据文件
│   ├── stats.json
│   ├── nodes.json
│   ├── activities.json
│   └── sentiment.json
└── scripts/            # 自动化脚本
    └── scrape.js       # 数据采集脚本
```

## 🚀 快速分享

### 方法1：直接发送文件（最简单）

`share.html` 是一个独立的单文件，包含所有数据和样式：
- 直接发送这个文件给别人
- 对方双击打开即可在浏览器中查看
- 文件位置：`monster-hunter-tracker/share.html`

### 方法2：部署到公网（推荐，支持自动更新）

#### 使用 Vercel 部署

1. 安装 Vercel CLI：
```bash
npm install -g vercel
```

2. 在项目目录执行：
```bash
cd monster-hunter-tracker
vercel
```

3. 按提示登录并部署，完成后会获得一个公网链接：
```
https://monster-hunter-tracker-xxx.vercel.app
```

#### 设置每日自动更新

使用 Windows 任务计划程序，每日10点自动采集数据并部署：

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每日 10:00
4. 操作：启动程序
   - 程序：`powershell.exe`
   - 参数：
   ```
   cd "C:\Users\yuyingjiang\WorkBuddy\20260331101524\monster-hunter-tracker"; node scripts/scrape.js; vercel --prod
   ```

### 方法3：GitHub Pages（免费静态托管）

1. 创建 GitHub 仓库
2. 上传项目文件
3. Settings → Pages → 选择 main 分支
4. 获得链接：`https://你的用户名.github.io/monster-hunter-tracker/share.html`

## 📊 数据更新

### 手动更新

```bash
cd monster-hunter-tracker
node scripts/scrape.js
```

### 自动更新（Windows）

创建任务计划，每日10点自动执行数据采集。

## 📋 当前数据（2026-04-02）

| 渠道 | 预约数 | 评分 | 排名 |
|------|--------|------|------|
| TapTap | 38万 | 7.3 | 预约榜 #5 |
| B站 | 14.1万 | 9.3 | 游戏预约榜 #2 |
| 好游快爆 | 13.4万 | 8.2 | 新游期待榜 #3 |
| 4399 | 6万+ | 9.2 | 预约榜 Top3 |
| **总计** | **71.5万** | - | - |

## 🔗 快速链接

- 官网：https://mho.qq.com/web202507/index.html
- TapTap：https://www.taptap.cn/app/243984
- B站官方账号：https://space.bilibili.com/xxxxx
