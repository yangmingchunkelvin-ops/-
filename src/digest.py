"""
AI × Marketing Daily Digest
每日 AI 营销资讯聚合 + 邮件推送
"""

import os
import json
import smtplib
import datetime
import feedparser
import requests
from google import genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# ─── 配置 ────────────────────────────────────────────────
SENDER_EMAIL    = os.environ["SENDER_EMAIL"]       # 发件 Gmail
SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]    # Gmail App Password
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]    # 收件邮箱
GEMINI_API_KEY  = os.environ["GEMINI_API_KEY"]     # Gemini API Key

TODAY = datetime.datetime.now(datetime.timezone.utc).strftime("%Y年%m月%d日")

# ─── RSS 源 ──────────────────────────────────────────────
RSS_FEEDS = [
    # AI 行业资讯
    {"name": "TechCrunch AI",      "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI",       "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "VentureBeat AI",     "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "MIT Tech Review",    "url": "https://www.technologyreview.com/feed/"},
    # 营销科技
    {"name": "Marketing Dive",     "url": "https://www.marketingdive.com/feeds/news/"},
    {"name": "AdExchanger",        "url": "https://www.adexchanger.com/feed/"},
    {"name": "Martech Alliance",   "url": "https://martechalliance.com/feed/"},
    # 融资/商业
    {"name": "Crunchbase News",    "url": "https://news.crunchbase.com/feed/"},
]

# 关键词过滤（命中至少一个才收录）
KEYWORDS = [
    "AI marketing", "artificial intelligence marketing", "generative AI", "gen AI",
    "marketing AI", "ad tech", "adtech", "martech", "marketing technology",
    "AI advertising", "programmatic", "creative AI", "content AI",
    "marketing automation", "AI campaign", "brand AI",
    "funding", "raises", "Series", "investment", "million",  # 融资相关
    "OpenAI", "Anthropic", "Google AI", "Meta AI", "Adobe AI",
]

KEYWORDS_LOWER = [k.lower() for k in KEYWORDS]


def fetch_rss_articles(max_per_feed: int = 8) -> list[dict]:
    """从 RSS 源抓取近 24 小时内的相关文章"""
    articles = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=28)

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:max_per_feed]:
                # 时间过滤
                pub = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub = datetime.datetime(*entry.published_parsed[:6],
                                           tzinfo=datetime.timezone.utc)
                if pub and pub < cutoff:
                    continue

                title   = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "")
                link    = getattr(entry, "link", "")

                # 关键词过滤
                text = (title + " " + summary).lower()
                if not any(kw in text for kw in KEYWORDS_LOWER):
                    continue

                # 清理 HTML
                clean_summary = BeautifulSoup(summary, "html.parser").get_text()[:300]

                articles.append({
                    "source":  feed_info["name"],
                    "title":   title,
                    "summary": clean_summary,
                    "link":    link,
                    "date":    pub.strftime("%m-%d %H:%M") if pub else "未知",
                })
        except Exception as e:
            print(f"[WARN] {feed_info['name']} 抓取失败: {e}")

    # 去重（按标题）
    seen, unique = set(), []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    print(f"[INFO] 共抓取 {len(unique)} 条相关文章")
    return unique


def summarize_with_gemini(articles: list[dict]) -> str:
    """用 Gemini 对文章做智能摘要和分类"""
    if not articles:
        return "<p>今日暂无符合条件的 AI × 营销资讯，明天见！</p>"

    client = genai.Client(api_key=GEMINI_API_KEY)

    articles_text = "\n\n".join([
        f"【{a['source']}】{a['date']}\n标题: {a['title']}\n摘要: {a['summary']}\n链接: {a['link']}"
        for a in articles
    ])

    prompt = f"""你是一位专注于 AI × 营销领域的资深分析师，请对以下今日抓取的资讯进行整理和点评。

原始文章列表：
{articles_text}

请按以下分类整理，每条资讯用中文写1-2句核心要点，并在末尾附上原文链接。
分类：
1. 🚀 AI 营销融资动态（初创公司融资、并购）
2. 🤖 AI × 营销新玩法（产品功能、营销案例、创意技术）
3. 🐦 行业大佬观点（科技/营销领域 KOL 的关键判断）
4. 📊 平台与工具动态（Meta、Google、TikTok 等广告平台 AI 能力更新）
5. 🌏 中国市场动态（国内 AI 营销相关）

要求：
- 每条用一个 emoji 点（▸）开头
- 如果某分类今日无内容，请跳过该分类
- 结尾用2-3句话写「今日编辑观察」，点出最值得关注的趋势
- 输出格式为 HTML（用 <h3>、<ul>、<li>、<p>、<a> 标签），适合邮件展示
- 链接用 target="_blank" 打开新标签页
- 不要输出 ```html 代码块，直接输出 HTML 内容"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
    )
    return response.text


def build_email_html(digest_html: str, article_count: int) -> str:
    """构建精美的邮件 HTML"""
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #f0f4f0; font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; }}
  .wrapper {{ max-width: 680px; margin: 32px auto; }}

  /* Header */
  .header {{
    background: linear-gradient(135deg, #005A50 0%, #00796B 60%, #00BFA5 100%);
    border-radius: 16px 16px 0 0;
    padding: 36px 40px 28px;
    color: white;
  }}
  .header-tag {{
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
  }}
  .header h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 6px; }}
  .header p {{ font-size: 13px; opacity: 0.8; }}
  .header-meta {{
    margin-top: 20px;
    display: flex;
    gap: 20px;
    font-size: 12px;
    opacity: 0.75;
  }}
  .header-meta span {{ display: flex; align-items: center; gap: 4px; }}

  /* Body */
  .body {{
    background: white;
    padding: 36px 40px;
  }}

  /* Digest content */
  .body h3 {{
    font-size: 15px;
    font-weight: 700;
    color: #1A2332;
    margin: 28px 0 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #f0f4f0;
  }}
  .body h3:first-child {{ margin-top: 0; }}
  .body ul {{ list-style: none; padding: 0; }}
  .body li {{
    padding: 10px 0 10px 0;
    font-size: 13.5px;
    line-height: 1.7;
    color: #374151;
    border-bottom: 1px solid #f9fafb;
  }}
  .body li:last-child {{ border-bottom: none; }}
  .body a {{ color: #005A50; text-decoration: none; font-weight: 500; }}
  .body a:hover {{ text-decoration: underline; }}
  .body p {{ font-size: 13.5px; line-height: 1.7; color: #374151; margin: 10px 0; }}

  /* Editor note */
  .editor-note {{
    background: linear-gradient(135deg, #f0faf8, #e6f7f4);
    border-left: 4px solid #00BFA5;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin-top: 24px;
    font-size: 13px;
    color: #005A50;
    line-height: 1.7;
  }}

  /* Footer */
  .footer {{
    background: #1A2332;
    border-radius: 0 0 16px 16px;
    padding: 22px 40px;
    text-align: center;
    color: #6b7280;
    font-size: 11.5px;
    line-height: 1.8;
  }}
  .footer a {{ color: #00BFA5; text-decoration: none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="header-tag">AI × Marketing</div>
    <h1>每日营销科技简报</h1>
    <p>今天最值得关注的 AI × 营销动态，为你筛选整理</p>
    <div class="header-meta">
      <span>📅 {TODAY}</span>
      <span>📰 {article_count} 条资讯</span>
      <span>⚡ Gemini 智能摘要</span>
    </div>
  </div>

  <div class="body">
    {digest_html}
  </div>

  <div class="footer">
    本邮件由 GitHub Actions + Gemini API 自动生成<br>
    数据来源：TechCrunch · VentureBeat · AdExchanger · Crunchbase 等<br>
    <br>
    <a href="#">取消订阅</a> · <a href="#">查看历史</a>
  </div>
</div>
</body>
</html>"""


def send_email(html_content: str):
    """通过 Gmail SMTP 发送邮件"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ AI × 营销日报 · {TODAY}"
    msg["From"]    = f"AI营销简报 <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

    print(f"[INFO] 邮件已发送至 {RECIPIENT_EMAIL}")


def main():
    print(f"[INFO] 开始生成 {TODAY} 的 AI × 营销日报...")

    # 1. 抓取文章
    articles = fetch_rss_articles()

    # 2. Gemini 摘要
    print("[INFO] 正在用 Gemini 生成智能摘要...")
    digest_html = summarize_with_gemini(articles)

    # 3. 构建邮件
    email_html = build_email_html(digest_html, len(articles))

    # 4. 发送
    send_email(email_html)
    print("[INFO] 完成！")


if __name__ == "__main__":
    main()
