#!/usr/bin/env python3
"""
新闻资讯爬虫 - 支持多主题
用法: python fetcher.py [ai|iran_war|all]
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from html import unescape

# ============ 配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'ai-news')
IRAN_OUTPUT_DIR = os.path.join(BASE_DIR, 'iran-news')

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ============ AI 资讯源 ============
AI_SOURCES = [
    # 36氪
    {
        "name": "36氪",
        "url": "https://www.36kr.com/information/AI/",
        "type": "web",
        "selector": ".article-item,.kr-page-art-list li",
        "title_pattern": None,
    },
    # 虎嗅
    {
        "name": "虎嗅",
        "url": "https://www.huxiu.com/channel/103.html",
        "type": "web", 
        "selector": ".article-item,.mod-art",
        "title_pattern": None,
    },
    # 机器之心
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/",
        "type": "web",
        "selector": ".article-item,.post-item",
        "title_pattern": None,
    },
    # Wired AI
    {
        "name": "Wired",
        "url": "https://www.wired.com/tag/ai/",
        "type": "web",
        "selector": ".SummaryItemWrapper-iwvBff",
        "title_pattern": None,
    },
]

# ============ 伊朗战争资讯源 ============
IRAN_SOURCES = [
    # 新华社
    {
        "name": "新华社",
        "url": "https://www.xinhuanet.com/world/",
        "type": "web",
        "keywords": ["伊朗", "中东", "以色列", "战争"],
    },
    # 环球网
    {
        "name": "环球网",
        "url": "https://world.huanqiu.com/",
        "type": "web",
        "keywords": ["伊朗", "中东", "以色列"],
    },
    # 观察者网
    {
        "name": "观察者网",
        "url": "https://www.guancha.cn/international",
        "type": "web",
        "keywords": ["伊朗", "中东", "以色列"],
    },
    # BBC 中文
    {
        "name": "BBC中文",
        "url": "https://www.bbc.com/zhongwen/simp",
        "type": "web",
        "keywords": ["伊朗"],
    },
]

# ============ 辅助函数 ============
def fetch_url(url, encoding='utf-8'):
    """获取网页内容"""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode(encoding)
            return html
    except Exception as e:
        print(f"  ❌ 获取失败 {url}: {e}")
        return None

def extract_news_simple(html, source_name, keywords=None):
    """简单提取新闻（基于关键词）"""
    news_list = []
    
    # 移除脚本和样式
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    
    # 查找所有链接和标题
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', html, re.IGNORECASE)
    
    seen = set()
    for url, title in links[:50]:
        title = unescape(title.strip())
        title = re.sub(r'<[^>]+>', '', title).strip()
        
        if len(title) < 5 or title in seen:
            continue
            
        # 关键词过滤
        if keywords:
            title_lower = title.lower()
            if not any(kw.lower() in title_lower for kw in keywords):
                continue
        
        # 清理标题
        title = re.sub(r'\s+', ' ', title)
        if len(title) > 80:
            title = title[:80] + '...'
            
        if title not in seen:
            seen.add(title)
            news_list.append({
                "title": title,
                "url": url if url.startswith('http') else f"https://example.com{url}",
                "source": source_name,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "summary": ""
            })
    
    return news_list

def fetch_ai_news():
    """获取AI资讯"""
    print("🤖 正在获取 AI 资讯...")
    all_news = []
    
    for source in AI_SOURCES:
        print(f"  📡 抓取: {source['name']}")
        html = fetch_url(source['url'])
        if html:
            news = extract_news_simple(html, source['name'])
            all_news.extend(news[:5])  # 每个源最多5条
            print(f"     ✅ 获取 {len(news)} 条")
        time.sleep(1)
    
    # 去重
    seen = set()
    unique_news = []
    for n in all_news:
        if n['title'] not in seen:
            seen.add(n['title'])
            unique_news.append(n)
    
    return unique_news[:15]

def fetch_iran_news():
    """获取伊朗战争资讯"""
    print("⚔️ 正在获取伊朗战争资讯...")
    all_news = []
    
    for source in IRAN_SOURCES:
        keywords = source.get('keywords', [])
        print(f"  📡 抓取: {source['name']}")
        html = fetch_url(source['url'])
        if html:
            news = extract_news_simple(html, source['name'], keywords)
            all_news.extend(news[:5])
            print(f"     ✅ 获取 {len(news)} 条")
        time.sleep(1)
    
    # 去重
    seen = set()
    unique_news = []
    for n in all_news:
        if n['title'] not in seen:
            seen.add(n['title'])
            unique_news.append(n)
    
    return unique_news[:15]

def save_news(news, topic):
    """保存新闻到JSON"""
    if topic == 'ai':
        output_dir = OUTPUT_DIR
    else:
        output_dir = IRAN_OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存 latest.json
    latest_file = os.path.join(output_dir, 'latest.json')
    data = {
        "last_updated": datetime.now().isoformat(),
        "news_count": len(news),
        "topic": topic,
        "news": news
    }
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 保存带日期的归档
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_dir = os.path.join(output_dir, date_str)
    os.makedirs(date_dir, exist_ok=True)
    date_file = os.path.join(date_dir, 'index.html')
    
    # 生成HTML
    html = generate_html(news, topic)
    with open(date_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ {topic} 资讯已保存:")
    print(f"   📄 {latest_file}")
    print(f"   📄 {date_file}")
    
    return data

def generate_html(news, topic):
    """生成HTML页面"""
    title = "AI 资讯日报" if topic == 'ai' else "伊朗战争资讯"
    icon = "🤖" if topic == 'ai' else "⚔️"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{icon} {title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ text-align: center; margin-bottom: 10px; font-size: 2rem; }}
        .meta {{ text-align: center; color: rgba(255,255,255,0.6); margin-bottom: 40px; }}
        .news-list {{ display: flex; flex-direction: column; gap: 15px; }}
        .news-item {{
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s;
        }}
        .news-item:hover {{ background: rgba(255,255,255,0.15); transform: translateX(5px); }}
        .news-title {{ font-size: 1.1rem; margin-bottom: 8px; }}
        .news-title a {{ color: white; text-decoration: none; }}
        .news-title a:hover {{ color: #ffd700; }}
        .news-meta {{ font-size: 0.85rem; color: rgba(255,255,255,0.6); }}
        .news-summary {{ margin-top: 10px; font-size: 0.9rem; color: rgba(255,255,255,0.8); }}
        .back-link {{ 
            display: inline-block; 
            margin-bottom: 30px; 
            color: rgba(255,255,255,0.7); 
            text-decoration: none;
        }}
        .back-link:hover {{ color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← 返回首页</a>
        <h1>{icon} {title}</h1>
        <p class="meta">📅 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="news-list">
"""
    
    for item in news:
        html += f"""            <div class="news-item">
                <div class="news-title">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                </div>
                <div class="news-meta">{item['source']} • {item['time']}</div>
"""
        if item.get('summary'):
            html += f'                <div class="news-summary">{item["summary"]}</div>\n'
        html += """            </div>\n"""
    
    html += """        </div>
    </div>
</body>
</html>"""
    
    return html

def main():
    import sys
    
    topic = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    print(f"📰 资讯抓取工具 | 主题: {topic}")
    print("=" * 50)
    
    if topic in ('ai', 'all'):
        news = fetch_ai_news()
        save_news(news, 'ai')
    
    if topic in ('iran_war', 'iran', 'all'):
        news = fetch_iran_news()
        save_news(news, 'iran_war')
    
    print("\n🎉 全部完成!")

if __name__ == "__main__":
    main()