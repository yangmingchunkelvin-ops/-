# ⚡ AI × 营销每日简报

> 每天早上 8 点，自动推送 AI × 营销领域最新动态到你的邮箱。
> 零运维 · 免费 · GitHub Actions 驱动 · Claude AI 智能摘要

---

## 📬 邮件内容包含

- 🚀 AI 营销公司融资动态
- 🤖 AI × 营销新玩法 / 产品案例
- 🐦 行业大佬观点（科技 / 营销 KOL）
- 📊 广告平台 AI 能力更新（Meta / Google / TikTok）
- 🌏 中国市场动态
- ✍️ 编辑观察（Claude 生成的趋势判断）

---

## 🚀 部署教程（10 分钟完成）

### 第一步：Fork 这个仓库

点击右上角 **Fork** 按钮，复制到你自己的 GitHub 账号下。

---

### 第二步：准备 Gmail App Password

> ⚠️ 不能直接用 Gmail 密码，需要生成专用的 App Password

1. 打开 [myaccount.google.com/security](https://myaccount.google.com/security)
2. 确保已开启「两步验证」
3. 搜索 **App passwords**（应用专用密码）
4. 选择「邮件」→「其他设备」→ 填写名称 `AI Digest`
5. 点击生成，复制那个 **16 位密码**（格式：xxxx xxxx xxxx xxxx）

---

### 第三步：准备 Anthropic API Key

1. 打开 [console.anthropic.com](https://console.anthropic.com)
2. 注册 / 登录账号
3. 进入 **API Keys** → 点击 **Create Key**
4. 复制 API Key（`sk-ant-...` 开头）

> 💰 费用参考：每次运行消耗约 $0.01-0.02，每月约 $0.5 以内

---

### 第四步：配置 GitHub Secrets

在你 Fork 的仓库页面：
**Settings → Secrets and variables → Actions → New repository secret**

依次添加以下 4 个 Secret：

| Secret 名称 | 填写内容 |
|---|---|
| `ANTHROPIC_API_KEY` | 你的 Claude API Key |
| `SENDER_EMAIL` | 用来发邮件的 Gmail 地址 |
| `SENDER_PASSWORD` | 第二步生成的 16 位 App Password（去掉空格） |
| `RECIPIENT_EMAIL` | 你想收邮件的地址（可以是任意邮箱） |

---

### 第五步：手动触发测试

1. 进入仓库 → **Actions** 标签页
2. 左侧点击 **AI Marketing Daily Digest**
3. 点击 **Run workflow** → **Run workflow**
4. 等待约 1-2 分钟
5. 检查你的收件箱 ✅

---

## ⚙️ 自定义配置

### 修改推送时间

编辑 `.github/workflows/daily-digest.yml` 中的 cron：

```yaml
# 默认：北京时间每天 8:00（UTC 0:00）
- cron: '0 0 * * *'

# 北京时间 7:30（UTC 23:30，前一天）
- cron: '30 23 * * *'
```

### 添加更多 RSS 源

编辑 `src/digest.py` 中的 `RSS_FEEDS` 列表，按格式添加新源即可。

### 修改关键词过滤

编辑 `src/digest.py` 中的 `KEYWORDS` 列表。

---

## 🛠 故障排查

| 问题 | 解决方案 |
|---|---|
| 邮件未收到 | 检查垃圾邮件文件夹 |
| Actions 运行失败 | 检查 Secrets 是否填写正确 |
| Gmail 登录失败 | 确认使用的是 App Password，不是账号密码 |
| 文章数量为 0 | RSS 源可能暂时不可用，次日自动恢复 |

---

## 📄 License

MIT — 自由使用和修改
