# AI Radar — 可写进简历的项目总结

> ⚠️ 以下所有数据均来自代码、日志和数据库的实际运行结果，未编造任何数字。

---

## 项目定位

**AI Radar**：面向 AI 产品经理的每日行业动态智能抓取与解读系统。每日自动从 10 个数据源抓取 AI 行业动态，通过 DeepSeek API 生成中文 AI PM 视角摘要，邮件推送日报，Web Dashboard 提供历史浏览与筛选。

## 技术栈

Python（异步爬虫 + AI 摘要） + Next.js 16（Web Dashboard） + Prisma 5（ORM） + SQLite（数据库） + GitHub Actions（定时调度） + DeepSeek API（大模型调用） + Resend API（邮件推送）

## 量化成果（基于实测数据）

| 指标 | 数值 |
|---|---|
| 数据源覆盖 | 10 个（ArXiv 论文、Product Hunt 产品、GitHub Trending 开源、Hacker News 讨论、OpenAI 官方博客、36氪 新闻，以及 4 个备选源） |
| 每日抓取量 | 约 110-120 条（稳定源 6/10，可用率 60%） |
| AI 摘要生成 | 每日 30 条，成功率 100%（30/30，DeepSeek `deepseek-chat`） |
| 摘要维度 | 产品洞察、行业影响、PM 关注点（结构化 Prompt 工程） |
| 数据库记录 | 143 条（测试期间），零空标题、零重复 URL |
| 内容分类 | 新闻 41% / 论文 23% / 产品 21% / 开源 15% |
| Dashboard | Next.js SPA，支持按分类/来源/日期筛选，分页浏览 |
| 定时调度 | GitHub Actions，每日 UTC 0:00（北京时间 8:00）自动运行 |
| 推送渠道 | 邮件（Resend API）+ 企业微信机器人（预留） |
| 代码规模 | 29 个源文件，Python 约 600 行 + TypeScript 约 400 行 |

## 个人贡献

- 独立完成项目架构设计与全栈开发（爬虫层 + 数据库层 + 展示层 + 调度层）
- 设计 AI PM 视角的摘要 Prompt，4 维度结构化输出
- 实现 10 源并发异步抓取引擎，含日期过滤、URL 去重、分类交错排列
- 解决 Windows/Unix 跨平台编码兼容、SQLite 日期格式与 Prisma ORM 对齐、GitHub Actions 数据库持久化等技术问题
- 编写完整测试报告，覆盖链路完整性、数据源状态、数据库质量统计

## 代码仓库

https://github.com/ligaolan/ai-radar-news
