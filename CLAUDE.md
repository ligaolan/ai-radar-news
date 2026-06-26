# AI Radar

AI 行业每日动态抓取与智能摘要系统。每日自动抓取 10+ 数据源 → AI PM 视角摘要 → 邮件/企微推送 → Web Dashboard 浏览。

## 架构

```
Python Crawler → SQLite DB ← Next.js Dashboard
       ↓              ↓
  DeepSeek API    邮件推送(Resend)
  (AI 摘要)       企微机器人
```

## 常用命令

```bash
# 开发
npm run dev              # 启动 Next.js Dashboard (localhost:3000)

# 数据库
npm run db:push          # 同步 Prisma Schema → SQLite

# 爬虫
cd crawler && python main.py --dry-run   # 测试抓取（不写入DB）
cd crawler && python main.py             # 完整运行（抓取+摘要+推送）
cd crawler && python main.py --no-push   # 跳过推送
```

## 数据源

| 源 | 类型 | 抓取方式 |
|---|---|---|
| Hacker News | 新闻 | hnrss.org RSS |
| ArXiv | 论文 | arXiv API |
| GitHub Trending | 开源 | 网页解析 |
| Product Hunt | 产品 | RSS |
| OpenAI / Anthropic / Google AI | 博客 | RSS |
| 机器之心 / 量子位 / 36氪 AI | 中文媒体 | RSSHub RSS |

## 环境变量

复制 `.env.example` 为 `.env`，填写：
- `DEEPSEEK_API_KEY` — AI 摘要（必填）
- `RESEND_API_KEY` / `RESEND_FROM` / `RESEND_TO` — 邮件推送（可选）
- `WECHAT_WEBHOOK_URL` — 企微推送（可选）
- `DATABASE_URL` — SQLite 路径（默认 `file:./dev.db`）

## 定时调度

GitHub Actions 每日 UTC 0:00 自动运行。需在 GitHub Secrets 配置上述环境变量。
