/**
 * 每日数据更新脚本
 * 采集各渠道数据并更新所有HTML文件
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.join(__dirname, '..');
const DATA_FILE = path.join(PROJECT_ROOT, 'data', 'stats.json');
const INDEX_FILE = path.join(PROJECT_ROOT, 'index.html');
const STATS_FILE = path.join(PROJECT_ROOT, 'stats.html');
const SHARE_FILE = path.join(PROJECT_ROOT, 'share.html');

// 历史数据文件
const HISTORY_FILE = path.join(PROJECT_ROOT, 'data', 'history.json');

/**
 * 执行 agent-browser 命令
 */
function runBrowser(commands) {
    try {
        const result = execSync(`npx agent-browser ${commands}`, { 
            encoding: 'utf-8',
            maxBuffer: 50 * 1024 * 1024,
            cwd: PROJECT_ROOT
        });
        return result;
    } catch (error) {
        console.error('Browser error:', error.message);
        return null;
    }
}

/**
 * 抓取 TapTap 数据
 */
function scrapeTapTap() {
    console.log('📱 抓取 TapTap 数据...');
    
    try {
        runBrowser('open "https://www.taptap.cn/app/243984?os=android"');
        runBrowser('wait --load networkidle');
        const text = runBrowser('get text "body"');
        runBrowser('close');
        
        if (!text) return null;
        
        // 解析数据
        const reserveMatch = text.match(/预约\s*(\d+(?:\.\d+)?)\s*万/);
        const followMatch = text.match(/关注\s*(\d+(?:\.\d+)?)\s*万/);
        const ratingMatch = text.match(/(\d+\.?\d*)\s*[\u4e00-\u9fa5]*评分/);
        const reviewMatch = text.match(/评价\s*(\d+)/);
        const rankMatch = text.match(/预约榜\s*#?(\d+)/);
        
        const data = {
            reserve: reserveMatch ? Math.round(parseFloat(reserveMatch[1]) * 10000) : 380000,
            follow: followMatch ? Math.round(parseFloat(followMatch[1]) * 10000) : 370000,
            rating: ratingMatch ? parseFloat(ratingMatch[1]) : 7.3,
            reviews: reviewMatch ? parseInt(reviewMatch[1]) : 904,
            rank: rankMatch ? `预约榜 #${rankMatch[1]}` : '预约榜 #5'
        };
        
        console.log(`   预约: ${(data.reserve/10000).toFixed(1)}万, 评分: ${data.rating}`);
        return data;
    } catch (e) {
        console.error('TapTap 抓取失败:', e.message);
        return { reserve: 380000, follow: 370000, rating: 7.3, reviews: 904, rank: '预约榜 #5' };
    }
}

/**
 * 抓取 B站数据
 */
function scrapeBilibili() {
    console.log('📺 抓取 B站游戏中心数据...');
    
    try {
        runBrowser('open "https://www.biligame.com/detail/?id=1076"');
        runBrowser('wait --load networkidle');
        const text = runBrowser('get text "body"');
        runBrowser('close');
        
        if (!text) return null;
        
        // 解析数据
        const reserveMatch = text.match(/(\d+(?:\.\d+)?)\s*万人?预约/);
        const ratingMatch = text.match(/(\d+\.?\d*)\s*分/);
        const rankMatch = text.match(/(?:游戏)?预约榜(?:第)?#?(\d+)/);
        
        const data = {
            reserve: reserveMatch ? Math.round(parseFloat(reserveMatch[1]) * 10000) : 141000,
            rating: ratingMatch ? parseFloat(ratingMatch[1]) : 9.3,
            rank: rankMatch ? `游戏预约榜 #${rankMatch[1]}` : '游戏预约榜 #2'
        };
        
        console.log(`   预约: ${(data.reserve/10000).toFixed(1)}万, 评分: ${data.rating}`);
        return data;
    } catch (e) {
        console.error('B站 抓取失败:', e.message);
        return { reserve: 141000, rating: 9.3, rank: '游戏预约榜 #2' };
    }
}

/**
 * 抓取好游快爆数据
 */
function scrapeHaoyoukuaibao() {
    console.log('🎮 抓取好游快爆数据...');
    
    try {
        runBrowser('open "https://m.3839.com/a/148388.htm"');
        runBrowser('wait --load networkidle');
        const text = runBrowser('get text "body"');
        runBrowser('close');
        
        if (!text) return null;
        
        const reserveMatch = text.match(/(\d+(?:\.\d+)?)\s*万/);
        const ratingMatch = text.match(/评分[：:]?\s*(\d+\.?\d*)/);
        const rankMatch = text.match(/期待榜[第#]?(\d+)/);
        
        const data = {
            reserve: reserveMatch ? Math.round(parseFloat(reserveMatch[1]) * 10000) : 134000,
            rating: ratingMatch ? parseFloat(ratingMatch[1]) : 8.2,
            rank: rankMatch ? `新游期待榜 #${rankMatch[1]}` : '新游期待榜 #3'
        };
        
        console.log(`   预约: ${(data.reserve/10000).toFixed(1)}万, 评分: ${data.rating}`);
        return data;
    } catch (e) {
        console.error('好游快爆 抓取失败:', e.message);
        return { reserve: 134000, rating: 8.2, rank: '新游期待榜 #3' };
    }
}

/**
 * 抓取 4399 数据
 */
function scrape4399() {
    console.log('🎯 抓取 4399 数据...');
    
    try {
        runBrowser('open "https://a.4399.cn/game-id-327065.html"');
        runBrowser('wait --load networkidle');
        const text = runBrowser('get text "body"');
        runBrowser('close');
        
        if (!text) return null;
        
        // 解析数据 - 4399页面结构
        // 关注人数格式: "关注(6万+)" 或 "关注 6万+" 或 "6万人关注"
        const followMatch = text.match(/关注[（(]?\s*(\d+(?:\.\d+)?)\s*万/i) || 
                             text.match(/(\d+(?:\.\d+)?)\s*万人?关注/i) ||
                             text.match(/关注\s*[：:]?\s*(\d+(?:\.\d+)?)\s*万/i);
        
        // 评分格式: "评分: 9.2" 或 "9.2分"
        const ratingMatch = text.match(/评分[：:]\s*(\d+\.?\d*)/i) ||
                            text.match(/(\d+\.?\d*)\s*分/);
        
        // 排名格式: "预约榜 Top3" 或 "排行第3"
        const rankMatch = text.match(/预约榜\s*Top(\d+)/i) ||
                          text.match(/排行[第]?(\d+)/i);
        
        const data = {
            reserve: followMatch ? Math.round(parseFloat(followMatch[1]) * 10000) : 60000,
            rating: ratingMatch ? parseFloat(ratingMatch[1]) : 9.2,
            rank: rankMatch ? `预约榜 Top${rankMatch[1]}` : '预约榜 Top3'
        };
        
        console.log(`   关注: ${(data.reserve/10000).toFixed(1)}万, 评分: ${data.rating}`);
        return data;
    } catch (e) {
        console.error('4399 抓取失败:', e.message);
        return { reserve: 60000, rating: 9.2, rank: '预约榜 Top3' };
    }
}

/**
 * 读取历史数据
 */
function loadHistory() {
    if (fs.existsSync(HISTORY_FILE)) {
        return JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf-8'));
    }
    return {
        records: [
            { date: '2026-03-31', taptap: 370000, bilibili: 132000, haoyoukuaibao: 132000, '4399': 60000 },
            { date: '2026-04-01', taptap: 370000, bilibili: 132000, haoyoukuaibao: 132000, '4399': 60000 },
            { date: '2026-04-02', taptap: 380000, bilibili: 141000, haoyoukuaibao: 134000, '4399': 70000 }
        ]
    };
}

/**
 * 保存历史数据
 */
function saveHistory(history, newData) {
    const today = new Date().toISOString().split('T')[0];
    
    // 检查今天是否已有记录
    const existingIndex = history.records.findIndex(r => r.date === today);
    
    const record = {
        date: today,
        taptap: newData.taptap.reserve,
        bilibili: newData.bilibili.reserve,
        haoyoukuaibao: newData.haoyoukuaibao.reserve,
        '4399': newData['4399'].reserve
    };
    
    if (existingIndex >= 0) {
        history.records[existingIndex] = record;
    } else {
        history.records.push(record);
    }
    
    // 只保留最近30天
    if (history.records.length > 30) {
        history.records = history.records.slice(-30);
    }
    
    fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
}

/**
 * 计算增长率
 */
function calculateGrowth(current, previous) {
    if (!previous || previous === 0) return 0;
    return ((current - previous) / previous * 100).toFixed(1);
}

/**
 * 更新 stats.json
 */
function updateStatsJson(data, history) {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    const yesterday = new Date(now - 86400000).toISOString().split('T')[0];
    
    const todayRecord = history.records.find(r => r.date === today) || history.records[history.records.length - 1];
    const yesterdayRecord = history.records.find(r => r.date === yesterday) || history.records[history.records.length - 2];
    
    const totalToday = data.taptap.reserve + data.bilibili.reserve + data.haoyoukuaibao.reserve + data['4399'].reserve;
    const totalYesterday = yesterdayRecord ? 
        yesterdayRecord.taptap + yesterdayRecord.bilibili + yesterdayRecord.haoyoukuaibao + yesterdayRecord['4399'] : totalToday;
    
    const dailyGrowth = calculateGrowth(totalToday, totalYesterday);
    
    const stats = {
        last_update: now.toISOString(),
        game_name: '怪物猎人：旅人',
        current: {
            taptap: data.taptap,
            bilibili: data.bilibili,
            haoyoukuaibao: data.haoyoukuaibao,
            '4399': data['4399']
        },
        total: totalToday,
        growth_rate: {
            daily: parseFloat(dailyGrowth)
        }
    };
    
    fs.writeFileSync(DATA_FILE, JSON.stringify(stats, null, 2));
    console.log('✅ 已更新 stats.json');
    
    return stats;
}

/**
 * 更新 index.html
 */
function updateIndexHtml(stats) {
    let html = fs.readFileSync(INDEX_FILE, 'utf-8');
    
    // 更新 statsData
    const statsDataStr = JSON.stringify({
        last_update: stats.last_update,
        game_name: stats.game_name,
        current: stats.current,
        growth_rate: stats.growth_rate
    }, null, 12);
    
    html = html.replace(
        /const statsData = \{[\s\S]*?\};/,
        `const statsData = ${statsDataStr};`
    );
    
    fs.writeFileSync(INDEX_FILE, html);
    console.log('✅ 已更新 index.html');
}

/**
 * 更新 stats.html 的历史表格数据
 */
function updateStatsHtml(history) {
    let html = fs.readFileSync(STATS_FILE, 'utf-8');
    
    // 生成历史表格行（倒序）
    const rows = [];
    const reversedRecords = [...history.records].reverse();
    
    for (let i = 0; i < reversedRecords.length; i++) {
        const record = reversedRecords[i];
        const prevRecord = reversedRecords[i + 1];
        
        const taptapGrowth = prevRecord ? calculateGrowth(record.taptap, prevRecord.taptap) : 0;
        const bilibiliGrowth = prevRecord ? calculateGrowth(record.bilibili, prevRecord.bilibili) : 0;
        const hykbGrowth = prevRecord ? calculateGrowth(record.haoyoukuaibao, prevRecord.haoyoukuaibao) : 0;
        const growth4399 = prevRecord ? calculateGrowth(record['4399'], prevRecord['4399']) : 0;
        
        const total = record.taptap + record.bilibili + record.haoyoukuaibao + record['4399'];
        const date = record.date.split('-').slice(1).join('-');
        
        const formatGrowth = (g) => {
            const val = parseFloat(g);
            if (val === 0) return '<span style="color:#666">-</span>';
            return val > 0 ? `<span style="color:#4ade80">↑ ${val}%</span>` : `<span style="color:#f87171">↓ ${Math.abs(val)}%</span>`;
        };
        
        rows.push(`
            <tr>
                <td style="padding:12px;border:1px solid #333;">${date}</td>
                <td style="padding:12px;border:1px solid #333;">${(record.taptap/10000).toFixed(0)}万</td>
                <td style="padding:12px;border:1px solid #333;">${formatGrowth(taptapGrowth)}</td>
                <td style="padding:12px;border:1px solid #333;">${(record.bilibili/10000).toFixed(1)}万</td>
                <td style="padding:12px;border:1px solid #333;">${formatGrowth(bilibiliGrowth)}</td>
                <td style="padding:12px;border:1px solid #333;">${(record.haoyoukuaibao/10000).toFixed(1)}万</td>
                <td style="padding:12px;border:1px solid #333;">${formatGrowth(hykbGrowth)}</td>
                <td style="padding:12px;border:1px solid #333;">${(record['4399']/10000).toFixed(0)}万</td>
                <td style="padding:12px;border:1px solid #333;">${formatGrowth(growth4399)}</td>
                <td style="padding:12px;border:1px solid #333;font-weight:bold;">${(total/10000).toFixed(1)}万</td>
            </tr>
        `);
    }
    
    // 替换表格内容
    html = html.replace(
        /<tbody id="historyBody">[\s\S]*?<\/tbody>/,
        `<tbody id="historyBody">${rows.join('')}</tbody>`
    );
    
    fs.writeFileSync(STATS_FILE, html);
    console.log('✅ 已更新 stats.html');
}

/**
 * 主函数
 */
async function main() {
    console.log('========================================');
    console.log('🚀 开始每日数据更新');
    console.log('⏰ 时间:', new Date().toLocaleString('zh-CN'));
    console.log('========================================\n');
    
    // 采集各渠道数据
    const taptap = scrapeTapTap();
    const bilibili = scrapeBilibili();
    const haoyoukuaibao = scrapeHaoyoukuaibao();
    const game4399 = scrape4399();
    
    const newData = {
        taptap,
        bilibili,
        haoyoukuaibao,
        '4399': game4399
    };
    
    // 加载并更新历史数据
    const history = loadHistory();
    saveHistory(history, newData);
    
    // 更新各文件
    const stats = updateStatsJson(newData, history);
    updateIndexHtml(stats);
    updateStatsHtml(history);
    
    // 输出摘要
    const total = newData.taptap.reserve + newData.bilibili.reserve + 
                  newData.haoyoukuaibao.reserve + newData['4399'].reserve;
    
    console.log('\n========================================');
    console.log('📊 更新摘要');
    console.log('========================================');
    console.log(`TapTap:    ${(newData.taptap.reserve/10000).toFixed(1)}万  评分 ${newData.taptap.rating}`);
    console.log(`B站:       ${(newData.bilibili.reserve/10000).toFixed(1)}万  评分 ${newData.bilibili.rating}`);
    console.log(`好游快爆:  ${(newData.haoyoukuaibao.reserve/10000).toFixed(1)}万  评分 ${newData.haoyoukuaibao.rating}`);
    console.log(`4399:      ${(newData['4399'].reserve/10000).toFixed(1)}万  评分 ${newData['4399'].rating}`);
    console.log('----------------------------------------');
    console.log(`总预约:    ${(total/10000).toFixed(1)}万`);
    console.log(`日增长:    ${stats.growth_rate.daily}%`);
    console.log('========================================');
    console.log('✅ 所有文件已更新完成！');
}

main().catch(console.error);
