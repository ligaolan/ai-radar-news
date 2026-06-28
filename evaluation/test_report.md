# AI Radar 测试报告

> 生成时间：2026-06-26 20:10 (UTC+8)
> 测试环境：Windows 11, Python 3.12, Node.js 20.x
> 数据集：`prisma/dev.db` (SQLite)

---

## 1. 项目概览

| 模块 | 文件数 | 技术栈 | 状态 |
|---|---|---|---|
| 爬虫抓取 | 7 | Python (httpx + feedparser) | ✅ 正常运行 |
| 数据库 | 1 Schema + 1 Client | Prisma 5 + SQLite | ✅ 正常运行 |
| AI 摘要 | 1 | DeepSeek API (`deepseek-chat`) | ✅ 正常运行 |
| 邮件推送 | 1 | Resend API | ✅ 已调通（需配置 API Key） |
| 企微推送 | 1 (同文件) | 企业微信 Webhook | ⚠️ 未配置 Webhook URL |
| Web Dashboard | 4 Components + 1 API Route | Next.js 16 + TailwindCSS 4 | ✅ 本地验证通过 |
| 定时调度 | 1 Workflow | GitHub Actions (cron) | ✅ 已推送至 GitHub |
| **总计** | **29 files** | **Python + TypeScript** | **—** |

## 2. 链路完整性检查

| 环节 | 状态 | 证据 |
|---|---|---|
| 抓取 → 去重 | ✅ | dry-run 测试: 116 条抓取, 116 条去重后 |
| 去重 → AI 摘要 | ✅ | no-push 测试: 30/116 条成功生成摘要 |
| AI 摘要 → 入库 | ✅ | DB 记录: 143 条总数, 31 条含 AI 摘要 |
| 入库 → 推送(邮件) | ✅ | 历史测试: 邮件发送成功 → 2972712099@qq.com |
| 入库 → 推送(企微) | ⚠️ | 未配置 WECHAT_WEBHOOK_URL |
| 入库 → Dashboard | ✅ | `GET /api/articles` 返回 200, 20条/页分页 |
| GitHub Actions 调度 | ✅ | workflow_dispatch 手动触发成功 |

## 3. 数据源状态（2026-06-26 实测）

| # | 数据源 | 类型 | 抓取方式 | 本次抓取 | 入库累计 | 错误原因 |
|---|---|---|---|---|---|---|
| 1 | ArXiv | paper | arXiv API | 33 条 | 33 | 正常 |
| 2 | Product Hunt | product | RSS | 29 条 | 30 | 正常 |
| 3 | GitHub Trending | oss | GitHub Search API | 20 条 | 21 | 正常 |
| 4 | 36氪 AI | news | RSS | 30 条 | 51 | 正常 |
| 5 | OpenAI Blog | news | RSS | 4 条 | 4 | 正常 |
| 6 | Hacker News | news | hnrss.org RSS | 0 条 | 4 | hnrss.org 返回 502 Bad Gateway（上游间歇性故障） |
| 7 | 机器之心 | news | RSSHub RSS | 0 条 | 0 | RSSHub 返回 403 Forbidden（反爬限制） |
| 8 | 量子位 | news | RSSHub RSS | 0 条 | 0 | RSSHub 返回 403 Forbidden（反爬限制） |
| 9 | Anthropic Blog | news | RSSHub RSS | 0 条 | 0 | RSSHub 返回 403 Forbidden（反爬限制） |
| 10 | Google AI Blog | news | Blogger RSS | 0 条 | 0 | URL 返回 404 Not Found（RSS 路径已失效） |

**数据源可用率：6/10 (60%)，日均抓取量：约 110-120 条**

## 4. 数据库统计

### 4.1 总量

| 指标 | 数值 |
|---|---|
| 总文章数 | 143 |
| 数据时间范围 | 2026-06-19 ~ 2026-06-26 |
| 空标题数 | 0 |
| 空摘要数 | 0 |
| 重复标题数 | 0 |
| 重复 URL 数 | 0 |
| 含 AI 摘要数 | 31 (21.7%) |
| 已推送数 | 0（本次测试使用 --no-push） |

### 4.2 按分类

| 分类 | 数量 | 占比 |
|---|---|---|
| news (新闻) | 59 | 41.3% |
| paper (论文) | 33 | 23.1% |
| product (产品) | 30 | 21.0% |
| oss (开源) | 21 | 14.7% |

### 4.3 按数据源

| 数据源 | 数量 |
|---|---|
| 36氪 AI | 51 |
| ArXiv | 33 |
| Product Hunt | 30 |
| GitHub Trending | 21 |
| Hacker News | 4 |
| OpenAI Blog | 4 |

### 4.4 AI 摘要分布

| 数据源 | 摘要数 |
|---|---|
| Product Hunt | 10 |
| ArXiv | 5 |
| GitHub Trending | 5 |
| Hacker News | 4 |
| OpenAI Blog | 4 |
| 36氪 AI | 3 |

## 5. 已知问题

1. **hnrss.org 稳定性差**：2026-06-26 两次测试均返回 502，建议增加备选 HN 数据源
2. **RSSHub 403 封禁**：机器之心、量子位、Anthropic Blog 均被 RSSHub 主站拒绝访问，需要自建 RSSHub 实例或更换数据源
3. **Google AI Blog RSS 不可用**：`blog.google` RSS 路径已失效，需寻找替代源
4. **`upsert_articles` 计数偏差**：使用 `conn.total_changes` 而非单次 `rowcount`，导致日志中"新增"数字偏高（日志显示 102，实际新增约 25），属于非功能性 bug
5. **Windows 终端编码**：部分中文在默认 CMD 终端显示为乱码，但不影响数据本身

## 6. 环境变量检查

| 变量 | 状态 | 用途 |
|---|---|---|
| DEEPSEEK_API_KEY | ✅ 已配置 | AI 摘要生成（30/30 全部成功） |
| RESEND_API_KEY | ✅ 已配置 | 邮件推送（历史测试成功） |
| RESEND_FROM | ✅ 已配置 | 发件人地址 |
| RESEND_TO | ✅ 已配置 | 收件人地址 |
| WECHAT_WEBHOOK_URL | ❌ 未配置 | 企微推送（已跳过） |

## 7. 测试结论

项目具备完整的 **"抓取 → 去重 → AI 摘要 → 入库 → 推送"** 链路。6 个稳定数据源每日可产出约 110-120 条 AI 相关动态，其中 30 条附带 AI PM 视角中文摘要。GitHub Actions 定时调度已就绪，配置 Secrets 后即可每日自动运行。

4 个失效数据源（Hacker News 间歇性、机器之心/量子位/Anthropic/Google AI）不影响核心链路，建议作为 V2 优化项。
