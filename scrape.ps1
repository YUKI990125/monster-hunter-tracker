# 《怪物猎人：旅人》渠道数据采集脚本 (PowerShell版本)
# 替代Python脚本，完成四大模块数据采集

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# 项目路径
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DATA_DIR = Join-Path $PROJECT_DIR "data"

# 确保数据目录存在
if (-not (Test-Path $DATA_DIR)) {
    New-Item -ItemType Directory -Path $DATA_DIR -Force | Out-Null
}

# HTTP请求头
$HEADERS = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    'Accept-Language' = 'zh-CN,zh;q=0.9,en;q=0.8'
}

# 获取页面内容
function Get-PageContent {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -Headers $HEADERS -TimeoutSec 20 -UseBasicParsing
        return $response.Content
    } catch {
        Write-Host "   ⚠️ 获取页面失败 $Url : $_" -ForegroundColor Yellow
        return $null
    }
}

# 解析数字（支持万、亿单位）
function Parse-Number {
    param([string]$Text)
    $Text = $Text.Trim()
    
    if ($Text -match '([\d.]+)\s*万') {
        return [math]::Floor([double]$matches[1] * 10000)
    }
    if ($Text -match '([\d.]+)\s*亿') {
        return [math]::Floor([double]$matches[1] * 100000000)
    }
    if ($Text -match '[\d,]+') {
        return [int]($matches[0] -replace ',', '')
    }
    return 0
}

# 解析日期
function Parse-Date {
    param([string]$Text)
    if ($Text -match '(\d{4})年(\d{1,2})月(\d{1,2})日') {
        return "{0}-{1:D2}-{2:D2}" -f [int]$matches[1], [int]$matches[2], [int]$matches[3]
    }
    if ($Text -match '(\d{4})-(\d{1,2})-(\d{1,2})') {
        return "{0}-{1:D2}-{2:D2}" -f [int]$matches[1], [int]$matches[2], [int]$matches[3]
    }
    return $null
}

# ==================== 模块1: 统计数据采集 ====================
function Collect-Stats {
    Write-Host "📊 [1/4] 采集预约/下载数据..." -ForegroundColor Cyan
    
    $stats = @{
        taptap = @{ reserve = 0; download = 0 }
        bilibili = @{ reserve = 0; download = 0; note = "" }
        haoyoukuaibao = @{ reserve = 0; download = 0 }
        "4399" = @{ reserve = 0; download = 0; note = "" }
    }
    
    # TapTap
    Write-Host "   正在采集TapTap数据..."
    $html = Get-PageContent "https://www.taptap.cn/app/243984"
    if ($html) {
        # 从HTML中提取预约数
        if ($html -match '预约[^\d]*([\d.]+\s*万)') {
            $stats.taptap.reserve = Parse-Number $matches[1]
        } elseif ($html -match '(\d+\.?\d*\s*万)[^\d]*人.*预约') {
            $stats.taptap.reserve = Parse-Number $matches[1]
        }
        # 尝试其他匹配模式
        if ($stats.taptap.reserve -eq 0) {
            if ($html -match 'class="[^"]*reserve[^"]*"[^>]*>([^<]+)') {
                $stats.taptap.reserve = Parse-Number $matches[1]
            }
        }
        Write-Host "   ✅ TapTap预约数: $($stats.taptap.reserve)"
    }
    
    # B站
    Write-Host "   正在采集B站数据..."
    $html = Get-PageContent "https://gwlrlr.biligame.com/gwlryykq"
    if ($html) {
        if ($html -match '预约[^\d]*([\d.]+\s*万?)') {
            $stats.bilibili.reserve = Parse-Number $matches[1]
        }
        Write-Host "   ✅ B站预约数: $($stats.bilibili.reserve)"
    }
    
    # 好游快爆
    Write-Host "   正在采集好游快爆数据..."
    $html = Get-PageContent "https://m.3839.com/a/148388.htm"
    if ($html) {
        if ($html -match '(\d+\.?\d*)\s*万?\s*预约') {
            $stats.haoyoukuaibao.reserve = Parse-Number $matches[1]
        } elseif ($html -match '预约人数[^\d]*([\d.]+\s*万?)') {
            $stats.haoyoukuaibao.reserve = Parse-Number $matches[1]
        }
        Write-Host "   ✅ 好游快爆预约数: $($stats.haoyoukuaibao.reserve)"
    }
    
    # 4399
    Write-Host "   正在采集4399数据..."
    $html = Get-PageContent "https://www.4399.com/pcgame/game/327065.html"
    if ($html) {
        if ($html -match '(\d+\.?\d*)\s*人?\s*(关注|预约)') {
            $stats."4399".reserve = Parse-Number $matches[1]
        }
        Write-Host "   ✅ 4399预约数: $($stats.'4399'.reserve)"
    }
    
    # 读取现有数据并更新
    $statsFile = Join-Path $DATA_DIR "stats.json"
    $data = @{}
    if (Test-Path $statsFile) {
        $data = Get-Content $statsFile -Raw | ConvertFrom-Json
    } else {
        $data = @{
            game_name = "怪物猎人：旅人"
            current = @{}
            history = @()
            growth_rate = @{}
        }
    }
    
    $now = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    $today = Get-Date -Format "yyyy-MM-dd"
    
    $data.current = @{
        taptap = @{ reserve = $stats.taptap.reserve; download = $stats.taptap.download; update_time = $now }
        bilibili = @{ reserve = $stats.bilibili.reserve; download = $stats.bilibili.download; update_time = $now; note = $stats.bilibili.note }
        haoyoukuaibao = @{ reserve = $stats.haoyoukuaibao.reserve; download = $stats.haoyoukuaibao.download; update_time = $now }
        "4399" = @{ reserve = $stats."4399".reserve; download = $stats."4399".download; update_time = $now; note = $stats."4399".note }
    }
    
    $totalReserve = $stats.taptap.reserve + $stats.bilibili.reserve + $stats.haoyoukuaibao.reserve + $stats."4399".reserve
    
    # 更新历史记录
    $history = @($data.history)
    $existingToday = $history | Where-Object { $_.date -eq $today }
    if (-not $existingToday) {
        $history += @{
            date = $today
            taptap_reserve = $stats.taptap.reserve
            bilibili_reserve = $stats.bilibili.reserve
            haoyoukuaibao_reserve = $stats.haoyoukuaibao.reserve
            reserve_4399 = $stats."4399".reserve
            total_reserve = $totalReserve
        }
    }
    $data.history = $history
    $data.last_update = $now
    
    $data | ConvertTo-Json -Depth 10 | Out-File $statsFile -Encoding UTF8
    Write-Host "   💾 统计数据已保存到 $statsFile"
    Write-Host "   📊 总预约数: $totalReserve"
    
    return $data
}

# ==================== 模块2: 节点数据采集 ====================
function Collect-Nodes {
    Write-Host "`n📌 [2/4] 采集节点数据..." -ForegroundColor Cyan
    
    $nodes = @{
        "预约开启" = @{ date = $null; time = $null; source = @(); status = "待定" }
        "测试招募" = @{ date = $null; time = $null; source = @(); status = "待定" }
        "测试开启" = @{ date = $null; time = $null; source = @(); status = "待定" }
        "测试结束" = @{ date = $null; time = $null; source = @(); status = "待定" }
        "公测首发定档" = @{ date = $null; time = $null; source = @(); status = "待定" }
        "前瞻直播" = @{ date = $null; time = $null; source = @(); status = "暂无" }
        "预注册" = @{ date = $null; time = $null; source = @(); status = "暂无" }
        "预下载" = @{ date = $null; time = $null; source = @(); status = "待定" }
        "公测开启" = @{ date = $null; time = $null; source = @(); status = "待定" }
    }
    
    $keywords = @{
        "预约开启" = @("预约开启", "预约现已开启", "预约正式开启")
        "测试招募" = @("测试招募", "体验团招募", "封闭测试招募", "首测招募")
        "测试开启" = @("测试开启", "首测开启", "封闭测试开启")
        "测试结束" = @("测试结束", "首测结束", "封闭测试结束")
        "公测首发定档" = @("公测定档", "首发定档", "上线时间")
        "前瞻直播" = @("前瞻直播", "发布会直播", "定档直播")
        "预注册" = @("预注册", "预注册开启")
        "预下载" = @("预下载", "预下载开启")
        "公测开启" = @("公测开启", "正式上线", "全平台公测")
    }
    
    # 采集官网
    Write-Host "   正在采集官网节点信息..."
    $html = Get-PageContent "https://mho.qq.com/web202507/index.html"
    if ($html) {
        foreach ($nodeType in $keywords.Keys) {
            foreach ($keyword in $keywords[$nodeType]) {
                if ($html -match [regex]::Escape($keyword)) {
                    $date = Parse-Date $html
                    if ($date) {
                        $nodes[$nodeType].date = $date
                        $nodes[$nodeType].status = "已确认"
                    }
                    if ($nodes[$nodeType].source -notcontains "官网") {
                        $nodes[$nodeType].source += "官网"
                    }
                    break
                }
            }
        }
        Write-Host "   ✅ 官网节点采集完成"
    }
    
    # 采集TapTap
    Write-Host "   正在采集TapTap节点信息..."
    $html = Get-PageContent "https://www.taptap.cn/app/243984/topic?type=official"
    if ($html) {
        foreach ($nodeType in $keywords.Keys) {
            foreach ($keyword in $keywords[$nodeType]) {
                if ($html -match [regex]::Escape($keyword)) {
                    $date = Parse-Date $html
                    if ($date -and -not $nodes[$nodeType].date) {
                        $nodes[$nodeType].date = $date
                        $nodes[$nodeType].status = "已确认"
                    }
                    if ($nodes[$nodeType].source -notcontains "TapTap") {
                        $nodes[$nodeType].source += "TapTap"
                    }
                    break
                }
            }
        }
        Write-Host "   ✅ TapTap节点采集完成"
    }
    
    # 保存数据
    $nodesFile = Join-Path $DATA_DIR "nodes.json"
    $data = @{
        game_name = "怪物猎人：旅人"
        nodes = $nodes
        last_update = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    }
    
    $data | ConvertTo-Json -Depth 10 | Out-File $nodesFile -Encoding UTF8
    Write-Host "   💾 节点数据已保存到 $nodesFile"
    
    return $nodes
}

# ==================== 模块3: 活动数据采集 ====================
function Collect-Activities {
    Write-Host "`n🎁 [3/4] 采集活动数据..." -ForegroundColor Cyan
    
    $rewardKeywords = @("页面活动", "定制", "链接")
    $communityKeywords = @("有奖活动", "即可成功参与活动", "已开奖")
    
    $rewardActivities = @()
    $communityActivities = @()
    
    # TapTap活动
    Write-Host "   正在采集TapTap活动..."
    $html = Get-PageContent "https://www.taptap.cn/app/243984/topic"
    if ($html) {
        # 简单提取活动信息
        foreach ($keyword in $rewardKeywords) {
            if ($html -match [regex]::Escape($keyword)) {
                $rewardActivities += @{
                    title = "TapTap活动 - $keyword"
                    channel = "TapTap"
                    url = "https://www.taptap.cn/app/243984/topic"
                    date = Parse-Date $html
                    keywords = @($keyword)
                }
                break
            }
        }
        foreach ($keyword in $communityKeywords) {
            if ($html -match [regex]::Escape($keyword)) {
                $communityActivities += @{
                    title = "TapTap社区活动"
                    channel = "TapTap"
                    url = "https://www.taptap.cn/app/243984/topic"
                    date = Parse-Date $html
                    keywords = @($keyword)
                }
                break
            }
        }
        Write-Host "   ✅ TapTap活动采集完成"
    }
    
    # 好游快爆活动
    Write-Host "   正在采集好游快爆活动..."
    $html = Get-PageContent "https://m.3839.com/a/148388.htm"
    if ($html) {
        foreach ($keyword in $rewardKeywords) {
            if ($html -match [regex]::Escape($keyword)) {
                $rewardActivities += @{
                    title = "好游快爆活动 - $keyword"
                    channel = "好游快爆"
                    url = "https://m.3839.com/a/148388.htm"
                    date = Parse-Date $html
                    keywords = @($keyword)
                }
                break
            }
        }
        Write-Host "   ✅ 好游快爆活动采集完成"
    }
    
    # 添加ID
    for ($i = 0; $i -lt $rewardActivities.Count; $i++) {
        $rewardActivities[$i].id = $i + 1
    }
    for ($i = 0; $i -lt $communityActivities.Count; $i++) {
        $communityActivities[$i].id = $i + 1
    }
    
    # 保存数据
    $activitiesFile = Join-Path $DATA_DIR "activities.json"
    $data = @{
        game_name = "怪物猎人：旅人"
        reward_activities = $rewardActivities
        community_activities = $communityActivities
        last_update = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    }
    
    $data | ConvertTo-Json -Depth 10 | Out-File $activitiesFile -Encoding UTF8
    Write-Host "   💾 活动数据已保存到 $activitiesFile"
    Write-Host "   🎁 有奖活动: $($rewardActivities.Count) 个"
    Write-Host "   🎮 社区活动: $($communityActivities.Count) 个"
    
    return $data
}

# ==================== 模块4: 舆情数据采集 ====================
function Collect-Sentiment {
    Write-Host "`n💬 [4/4] 采集舆情数据..." -ForegroundColor Cyan
    
    $positiveKeywords = @("期待", "画质好", "流畅", "还原", "好玩", "喜欢", "棒", "优秀", "不错", "推荐", "赞")
    $negativeKeywords = @("垃圾", "差", "失望", "坑", "卡顿", "bug", "无聊", "差评", "恶心")
    
    $reviews = @()
    $positiveCount = 0
    $negativeCount = 0
    $neutralCount = 0
    
    Write-Host "   正在采集TapTap评论..."
    $html = Get-PageContent "https://www.taptap.cn/app/243984/review"
    if ($html) {
        # 分析情感
        foreach ($kw in $positiveKeywords) {
            if ($html -match [regex]::Escape($kw)) {
                $positiveCount++
            }
        }
        foreach ($kw in $negativeKeywords) {
            if ($html -match [regex]::Escape($kw)) {
                $negativeCount++
            }
        }
        
        # 提取评论样本
        $commentMatches = [regex]::Matches($html, '期待[^\s<]{2,20}')
        foreach ($match in $commentMatches | Select-Object -First 3) {
            $reviews += $match.Value
        }
        
        Write-Host "   ✅ TapTap评论采集完成"
    }
    
    $total = $positiveCount + $negativeCount
    if ($total -gt 0) {
        $positivePct = [math]::Round($positiveCount / $total * 100, 1)
        $negativePct = [math]::Round($negativeCount / $total * 100, 1)
        $neutralPct = [math]::Round(100 - $positivePct - $negativePct, 1)
    } else {
        $positivePct = 0
        $negativePct = 0
        $neutralPct = 100
    }
    
    # 保存数据
    $sentimentFile = Join-Path $DATA_DIR "sentiment.json"
    $data = @{
        game_name = "怪物猎人：旅人"
        daily_reports = @(
            @{
                date = (Get-Date -Format "yyyy-MM-dd")
                summary = @{
                    positive = $positivePct
                    neutral = $neutralPct
                    negative = $negativePct
                    total_comments = $reviews.Count
                }
                positive_keywords = $positiveKeywords | Select-Object -First 5
                negative_keywords = $negativeKeywords | Select-Object -First 5
                sample_comments = $reviews
            }
        )
        history_summary = @{
            total_positive = $positivePct
            total_neutral = $neutralPct
            total_negative = $negativePct
            trend = "稳定"
            total_days = 1
        }
        last_update = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    }
    
    # 如果已有数据，合并历史
    if (Test-Path $sentimentFile) {
        $existing = Get-Content $sentimentFile -Raw | ConvertFrom-Json
        if ($existing.daily_reports) {
            $data.daily_reports = @($existing.daily_reports) + $data.daily_reports
        }
    }
    
    $data | ConvertTo-Json -Depth 10 | Out-File $sentimentFile -Encoding UTF8
    Write-Host "   💾 舆情数据已保存到 $sentimentFile"
    Write-Host "   👍 好评关键词: $positiveCount 个"
    Write-Host "   👎 差评关键词: $negativeCount 个"
    
    return $data
}

# ==================== 主程序 ====================
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "《怪物猎人：旅人》渠道数据采集 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Green

$results = @{
    run_time = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    status = @{}
    errors = @()
}

# 执行四大模块采集
try {
    $results.stats = Collect-Stats
    $results.status.stats = "success"
} catch {
    $results.status.stats = "failed"
    $results.errors += "统计数据采集失败: $_"
    Write-Host "   ❌ 统计数据采集失败: $_" -ForegroundColor Red
}

try {
    $results.nodes = Collect-Nodes
    $results.status.nodes = "success"
} catch {
    $results.status.nodes = "failed"
    $results.errors += "节点数据采集失败: $_"
    Write-Host "   ❌ 节点数据采集失败: $_" -ForegroundColor Red
}

try {
    $results.activities = Collect-Activities
    $results.status.activities = "success"
} catch {
    $results.status.activities = "failed"
    $results.errors += "活动数据采集失败: $_"
    Write-Host "   ❌ 活动数据采集失败: $_" -ForegroundColor Red
}

try {
    $results.sentiment = Collect-Sentiment
    $results.status.sentiment = "success"
} catch {
    $results.status.sentiment = "failed"
    $results.errors += "舆情数据采集失败: $_"
    Write-Host "   ❌ 舆情数据采集失败: $_" -ForegroundColor Red
}

# 输出汇总
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "📋 采集结果汇总:" -ForegroundColor Green
$successCount = ($results.status.Values | Where-Object { $_ -eq "success" }).Count
$totalCount = $results.status.Count
Write-Host "   成功: $successCount/$totalCount 模块" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })

if ($results.errors.Count -gt 0) {
    Write-Host "`n⚠️ 错误信息:" -ForegroundColor Yellow
    foreach ($error in $results.errors) {
        Write-Host "   - $error" -ForegroundColor Yellow
    }
}

Write-Host "`n✨ 数据采集完成！" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Green
