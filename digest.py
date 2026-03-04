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
    # ── 大厂官方博客（最高优先级）──
    {"name": "Google Ads Blog",         "url": "https://blog.google/products/ads/rss/"},
    {"name": "Google Marketing Blog",   "url": "https://marketingplatform.google.com/about/blog/feed/"},
    {"name": "Meta Business Blog",      "url": "https://www.facebook.com/business/news/rss/"},
    {"name": "Meta AI Blog",            "url": "https://ai.meta.com/blog/rss/"},
    {"name": "LinkedIn Marketing Blog", "url": "https://business.linkedin.com/marketing-solutions/blog/rss"},
    {"name": "Microsoft Advertising",   "url": "https://about.ads.microsoft.com/en/blog/rss"},
    {"name": "TikTok Business Blog",    "url": "https://newsroom.tiktok.com/rss/"},
    {"name": "Snap Newsroom",           "url": "https://newsroom.snap.com/rss.xml"},
    {"name": "Amazon Ads Blog",         "url": "https://advertising.amazon.com/blog/rss"},
    {"name": "Adobe Experience Blog",   "url": "https://business.adobe.com/blog/rss"},

    # ── AI 行业头部媒体 ──
    {"name": "TechCrunch AI",           "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "TechCrunch Marketing",    "url": "https://techcrunch.com/tag/marketing/feed/"},
    {"name": "The Verge AI",            "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "VentureBeat AI",          "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Wired Business",          "url": "https://www.wired.com/feed/category/business/latest/rss"},
    {"name": "MIT Tech Review AI",      "url": "https://www.technologyreview.com/feed/"},

    # ── 广告/营销科技专业媒体 ──
    {"name": "AdExchanger",             "url": "https://www.adexchanger.com/feed/"},
    {"name": "Digiday",                 "url": "https://digiday.com/feed/"},
    {"name": "Marketing Dive",          "url": "https://www.marketingdive.com/feeds/news/"},
    {"name": "AdAge",                   "url": "https://adage.com/rss.xml"},
    {"name": "AdWeek",                  "url": "https://www.adweek.com/feed/"},
    {"name": "The Drum",                "url": "https://www.thedrum.com/rss"},
    {"name": "Martech.org",             "url": "https://martech.org/feed/"},
    {"name": "Search Engine Land",      "url": "https://searchengineland.com/feed"},
    {"name": "Social Media Today",      "url": "https://www.socialmediatoday.com/rss/"},

    # ── 推特大V（通过 RSSHub）──
    {"name": "Twitter-Sam Altman",      "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/sama"},
    {"name": "Twitter-Zuckerberg",      "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/zuck"},
    {"name": "Twitter-Sundar Pichai",   "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/sundarpichai"},
    {"name": "Twitter-Yann LeCun",      "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/ylecun"},
    {"name": "Twitter-Demis Hassabis",  "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/demishassabis"},
    {"name": "Twitter-Marketing AI",    "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/marketingaiinst"},
    {"name": "Twitter-Benedict Evans",  "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/benedictevans"},
    {"name": "Twitter-Kara Swisher",    "url": "https://rss-hub-iota-ten.vercel.app/twitter/user/karaswisher"},

    # ── 微信公众号（通过 RSSHub）──
    {"name": "公众号-深响",              "url": "https://rss-hub-iota-ten.vercel.app/wechat/wemp/deephub"},
    {"name": "公众号-营销新引擎",         "url": "https://rss-hub-iota-ten.vercel.app/wechat/wemp/mktengine"},
    {"name": "公众号-AppGrowing",        "url": "https://rss-hub-iota-ten.vercel.app/wechat/wemp/appgrowing"},
    {"name": "公众号-传播体操",           "url": "https://rss-hub-iota-ten.vercel.app/wechat/wemp/chuanboticao"},
    {"name": "公众号-剁椒TMT",           "url": "https://rss-hub-iota-ten.vercel.app/wechat/wemp/duojiaotmt"},
    {"name": "公众号-科技新知",           "url": "https://rss-hub-iota-ten.vercel.app/wechat/wemp/kejixinzhi"},
    {"name": "Crunchbase News",         "url": "https://news.crunchbase.com/feed/"},
    {"name": "TechCrunch Startups",     "url": "https://techcrunch.com/category/startups/feed/"},
]

# 关键词过滤 —— 命中任意一个即收录
KEYWORDS = [
    # 核心主题
    "AI marketing", "AI advertising", "AI ad", "AI-powered ad",
    "generative AI", "gen AI", "genAI", "LLM advertising",
    "marketing AI", "ad tech AI", "adtech AI", "martech AI",
    "creative AI", "AI creative", "AI campaign", "AI targeting",
    "AI personalization", "AI audience", "AI bidding", "AI optimization",
    "programmatic AI", "AI media buying", "AI copywriting",
    "AI video ad", "AI image ad", "AI content marketing",

    # 大厂产品关键词
    "Performance Max", "Advantage+", "Smart Bidding", "Demand Gen",
    "Google Ads AI", "Meta AI", "Meta Advantage", "TikTok Symphony",
    "Amazon DSP", "Microsoft Advertising AI", "LinkedIn AI",
    "Snap AI", "Pinterest AI", "YouTube AI",

    # AI 营销创业公司常见词
    "ad generation", "creative automation", "dynamic creative",
    "AI influencer", "virtual influencer", "synthetic media",
    "brand safety AI", "attribution AI", "ad measurement AI",

    # 大厂高管/观点
    "Mark Zuckerberg", "Sundar Pichai", "Yann LeCun",
    "chief marketing officer", "CMO", "VP of Marketing",

    # 融资信号
    "raises", "funding", "Series A", "Series B", "Series C",
    "million", "billion", "valuation", "backed by", "investment",
    "acquires", "acquisition", "merger",
    # 中文关键词（公众号内容）
    "AI广告", "AI营销", "人工智能营销", "智能投放", "程序化广告",
    "大模型营销", "AIGC营销", "生成式AI", "AI创意", "智能创意",
    "巨量引擎", "磁力引擎", "腾讯广告", "阿里妈妈", "百度营销",
    "Meta广告", "谷歌广告", "TikTok广告", "出海营销",
    "融资", "亿元", "千万", "完成融资", "获投",
]

KEYWORDS_LOWER = [k.lower() for k in KEYWORDS]


def fetch_rss_articles(max_per_feed: int = 15) -> list[dict]:
    """从 RSS 源抓取近 48 小时内的相关文章"""
    articles = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)

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

    prompt = f"""你是一位专注于 AI × 广告营销领域的资深行业分析师。以下是今日从行业媒体抓取的原始资讯，请筛选并整理成一份高质量简报。

原始文章列表：
{articles_text}

【输出要求】
1. 必须输出至少 20 条资讯（如原始文章不足 20 条，可对重要文章做延伸分析补充）
2. 优先收录：Meta、Google、TikTok、Amazon、Microsoft、Snap 等大厂的 AI 广告产品动态
3. 优先收录：AI × 广告/营销领域创业公司的融资、产品发布、高管访谈
4. 每条资讯写 2-3 句中文点评，说清楚"发生了什么"+"为什么重要"
5. 如有高管原话或关键数据，必须引用

【分类格式】请按以下 5 个分类输出，每类至少 3 条：

1. 📊 大厂广告 AI 动态（Meta / Google / TikTok / Amazon 等平台产品更新、功能上线、数据披露）
2. 🚀 AI 营销创业公司（融资、产品发布、并购、高管变动）
3. 🎯 AI 创意与投放技术（AI 生成广告素材、动态创意、智能出价、受众定向新技术）
4. 🗣️ 高管观点与行业访谈（CMO/VP/创始人对 AI 营销的判断、预测、策略分享）
5. 🌏 中国市场动态（字节、腾讯、阿里、百度等国内平台 AI 广告进展）

【格式要求】
- 每条以 ▸ 开头，标题加粗，后接 2-3 句点评，末尾附原文链接
- 如果某分类今日确实无内容，写"暂无相关动态"
- 结尾单独写一个「📌 编辑观察」模块：用 3-5 句话点出本周 AI 广告领域最值得关注的结构性趋势
- 输出纯 HTML（使用 <h3>、<ul>、<li>、<p>、<strong>、<a> 标签），适合邮件渲染
- 所有链接加 target="_blank"
- 不要输出 ```html 代码块标记，直接输出 HTML"""

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
