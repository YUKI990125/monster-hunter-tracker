/**
 * 数据采集脚本
 * 使用 agent-browser 抓取各渠道预约数据
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 数据文件路径
const DATA_FILE = path.join(__dirname, '..', 'data', 'stats.json');

/**
 * 执行 agent-browser 命令
 */
function runBrowser(commands) {
    try {
        const result = execSync(`npx agent-browser ${commands}`, { 
            encoding: 'utf-8',
            maxBuffer: 50 * 1024 * 1024
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
async function scrapeTapTap() {
    console.log('📱 抓取 TapTap 数据...');
    
    runBrowser('open "https://www.taptap.cn/app/243984?os=android"');
    runBrowser('wait --load networkidle');
    const text = runBrowser('get text "body"');
    runBrowser('close');
    
    if (!text) return null;
    
    // 解析预约数
    const reserveMatch = text.match(/预约\s*(\d+(?:\.\d+)?)\s*万/);
    const followMatch = text.match(/关注\s*(\d+(?:\.\d+)?)\s*万/);
    const ratingMatch = text.match(/(\d+\.?\d*)\s*官方入驻/);
    const reviewMatch = text.match(/评价\s*(\d+)/);
    const rankMatch = text.match(/预约榜\s*#(\d+)/);
    
    return {
        reserve: reserveMatch ? parseFloat(reserveMatch[1]) * 10000 : 0,
        follow: followMatch ? parseFloat(followMatch[1]) * 10000 : 0,
        rating: ratingMatch ? parseFloat(ratingMatch[1]) : 0,
        reviews: reviewMatch ? parseInt(reviewMatch[1]) : 0,
        rank: rankMatch ? `预约榜 #${rankMatch[1]}` : '-'
    };
}

/**
 * 抓取 B站数据
 */
async function scrapeBilibili() {
    console.log('📺 抓取 B站游戏中心数据...');
    
    runBrowser('open "https://search.bilibili.com/all?keyword=怪物猎人旅人"');
    runBrowser('wait --load networkidle');
    const text = runBrowser('get text "body"');
    runBrowser('close');
    
    if (!text) return null;
    
    // 解析预约数
    const reserveMatch = text.match(/(\d+(?:\.\d+)?)\s*万人?预约/);
    const ratingMatch = text.match(/(\d+\.?\d*)\s*分/);
    const rankMatch = text.match(/游戏预约榜第(\d+)名/);
    
    return {
        reserve: reserveMatch ? parseFloat(reserveMatch[1]) * 10000 : 0,
        rating: ratingMatch ? parseFloat(ratingMatch[1]) : 0,
        rank: rankMatch ? `游戏预约榜 #${rankMatch[1]}` : '-'
    };
}

/**
 * 抓取好游快爆数据
 */
async function scrapeHaoyoukuaibao() {
    console.log('🎮 抓取好游快爆数据...');
    
    runBrowser('open "https://m.3839.com/a/148388.htm"');
    runBrowser('wait --load networkidle');
    const text = runBrowser('get text "body"');
    runBrowser('close');
    
    if (!text) return null;
    
    const reserveMatch = text.match(/(\d+(?:\.\d+)?)\s*万/);
    const ratingMatch = text.match(/评分[：:]?\s*(\d+\.?\d*)/);
    
    return {
        reserve: reserveMatch ? parseFloat(reserveMatch[1]) * 10000 : 0,
        rating: ratingMatch ? parseFloat(ratingMatch[1]) : 0,
        rank: '新游期待榜 #3'
    };
}

/**
 * 主函数
 */
async function main() {
    console.log('🚀 开始采集数据...');
    console.log('时间:', new Date().toLocaleString('zh-CN'));
    
    const results = {
        last_update: new Date().toISOString(),
        current: {}
    };
    
    // 抓取各渠道数据
    const taptap = await scrapeTapTap();
    if (taptap) results.current.taptap = taptap;
    
    const bilibili = await scrapeBilibili();
    if (bilibili) results.current.bilibili = bilibili;
    
    const hykb = await scrapeHaoyoukuaibao();
    if (hykb) results.current.haoyoukuaibao = hykb;
    
    // 4399 数据（保持不变）
    results.current['4399'] = {
        reserve: 60000,
        rating: 9.2,
        rank: '预约榜 Top3'
    };
    
    // 保存数据
    fs.writeFileSync(DATA_FILE, JSON.stringify(results, null, 2));
    console.log('✅ 数据已保存到:', DATA_FILE);
    
    // 打印摘要
    console.log('\n📊 数据摘要:');
    console.log('TapTap:', results.current.taptap?.reserve, '预约');
    console.log('B站:', results.current.bilibili?.reserve, '预约');
    console.log('好游快爆:', results.current.haoyoukuaibao?.reserve, '预约');
    
    const total = (results.current.taptap?.reserve || 0) +
                  (results.current.bilibili?.reserve || 0) +
                  (results.current.haoyoukuaibao?.reserve || 0) +
                  (results.current['4399']?.reserve || 0);
    console.log('总预约:', total);
}

main().catch(console.error);
