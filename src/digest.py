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


def fetch_rss_articles(max_per_feed: int = 8) -> list[dict]:
    """从 RSS 源抓取近 36 小时内的文章，用关键词做轻量预过滤后交给 Gemini"""
    articles = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=36)

    for feed_info in RSS_FEEDS:
        feed_count = 0
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:max_per_feed]:
                pub = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub = datetime.datetime(*entry.published_parsed[:6],
                                           tzinfo=datetime.timezone.utc)
                if pub and pub < cutoff:
                    continue

                title   = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "")
                link    = getattr(entry, "link", "")

                if not title:
                    continue

                # 轻量关键词预过滤：只过滤明显无关的内容
                # 推特/公众号源不过滤（source 含 Twitter 或 公众号）
                is_social = "Twitter" in feed_info["name"] or "公众号" in feed_info["name"]
                if not is_social:
                    text = (title + " " + summary).lower()
                    if not any(kw.lower() in text for kw in KEYWORDS):
                        continue

                clean_summary = BeautifulSoup(summary, "html.parser").get_text()[:300]

                articles.append({
                    "source":  feed_info["name"],
                    "title":   title,
                    "summary": clean_summary,
                    "link":    link,
                    "date":    pub.strftime("%m-%d %H:%M") if pub else "最新",
                })
                feed_count += 1

            print(f"[INFO] {feed_info['name']}: {feed_count} 条")
        except Exception as e:
            print(f"[WARN] {feed_info['name']} 失败: {e}")

    # 去重
    seen, unique = set(), []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    # 限制总量，避免超时（最多 80 条送给 Gemini）
    if len(unique) > 80:
        unique = unique[:80]

    print(f"[INFO] 预过滤后共 {len(unique)} 条，送入 Gemini 精筛")
    return unique


def filter_with_thinking(articles: list[dict], client) -> list[dict]:
    """第一步：用 3.1 Pro 思考模式严格筛选，只保留真正 AI × 营销相关的内容"""
    if not articles:
        return []

    articles_json = json.dumps([
        {"id": i, "source": a["source"], "title": a["title"], "summary": a["summary"][:200]}
        for i, a in enumerate(articles)
    ], ensure_ascii=False)

    filter_prompt = f"""你是一位 AI × 广告营销领域的专业编辑，负责对资讯做严格相关性筛选。

以下是 {len(articles)} 条原始文章（JSON 格式），请仔细判断每条是否真正属于「AI × 营销/广告」范畴。

【收录标准 —— 必须同时满足两个条件】
条件 1：与「营销/广告/品牌/电商增长」有直接关联
  ✅ 包括：广告投放、创意生产、用户增长、品牌传播、营销自动化、广告平台、电商广告
  ❌ 排除：纯 AI 技术研究、AI 政策法规、AI 医疗、AI 教育（除非明确提到营销应用场景）

条件 2：与「AI/大模型/自动化技术」有直接关联
  ✅ 包括：生成式 AI、LLM、机器学习在营销中的应用、AI 工具/产品、自动化投放
  ❌ 排除：传统数字营销（无 AI 元素）、纯商业新闻（无技术内容）

【典型收录案例】
✅ Meta 推出 AI 广告创意生成工具
✅ Google Performance Max 新增 AI 功能
✅ AI 营销创业公司完成融资
✅ CMO 谈 AI 在营销中的应用
✅ TikTok Symphony AI 视频广告新功能
✅ 巨量引擎 AI 投放能力升级

【典型排除案例】
❌ OpenAI 发布新版 GPT（纯技术，无营销场景）
❌ AI 监管政策新闻
❌ 传统广告公司业绩报告（无 AI 内容）
❌ 科技公司融资（与营销无关）

原始文章列表：
{articles_json}

请输出一个 JSON 数组，只包含符合条件的文章 id，例如：[0, 3, 7, 12]
只输出 JSON 数组，不要任何解释文字。"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=filter_prompt,
        config={"temperature": 0.1},
    )

    # 解析返回的 ID 列表
    try:
        raw = response.text.strip()
        # 清理可能的 markdown 代码块
        raw = raw.replace("```json", "").replace("```", "").strip()
        selected_ids = json.loads(raw)
        filtered = [articles[i] for i in selected_ids if i < len(articles)]
        print(f"[INFO] 思考模式筛选：{len(articles)} → {len(filtered)} 条（AI × 营销相关）")
        return filtered
    except Exception as e:
        print(f"[WARN] 筛选结果解析失败，使用全量文章: {e}")
        return articles


def summarize_with_gemini(articles: list[dict]) -> str:
    """第二步：用 3.1 Pro 生成高质量摘要"""
    if not articles:
        return "<p>今日暂无符合条件的 AI × 营销资讯，明天见！</p>"

    client = genai.Client(api_key=GEMINI_API_KEY)

    # 先用思考模式筛选
    filtered_articles = filter_with_thinking(articles, client)

    if not filtered_articles:
        return "<p>今日暂无符合条件的 AI × 营销资讯，明天见！</p>"

    articles_text = "\n\n".join([
        f"【{a['source']}】{a['date']}\n标题: {a['title']}\n摘要: {a['summary']}\n链接: {a['link']}"
        for a in filtered_articles
    ])

    prompt = f"""你是一位专注于 AI × 广告营销领域的资深行业分析师。

以下是已经过严格筛选的 {len(filtered_articles)} 条 AI × 营销相关资讯，请整理成一份高质量简报。

【输出要求】
- 总条数不少于 20 条（如不足 20 条，对重要文章做延伸分析补充）
- 每条写 2-3 句中文点评：说清楚「发生了什么」+「为什么对营销人重要」
- 推特内容先翻译原文再点评
- 如有高管原话或关键数据，必须引用

【分类】按以下 5 类输出，每类至少 3 条：

1. 📊 大厂广告 AI 动态（Meta / Google / TikTok / Amazon 等平台产品更新）
2. 🚀 AI 营销创业公司（融资、产品发布、并购、高管变动）
3. 🎯 AI 创意与投放技术（AI 生成广告、动态创意、智能出价新技术）
4. 🗣️ 大佬观点（推特原文翻译 + 点评、高管访谈摘要）
5. 🌏 中国市场动态（国内平台 AI 广告进展、公众号精选）

【格式】
- 每条以 ▸ 开头，**标题加粗**，后接点评，末尾：<a href="链接" target="_blank">原文链接</a>
- 某分类无内容时写「暂无」
- 结尾写 📌 编辑观察：3-5 句话总结今日最值得关注的结构性趋势
- 输出纯 HTML，使用 <h3><ul><li><p><strong><a> 标签
- 直接输出 HTML，不要加 ```html 标记

原始资讯：
{articles_text}"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
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
