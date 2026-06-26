"""AI Radar 每日抓取主程序

用法:
  python main.py                     # 抓取 + AI摘要 + 写入DB + 推送
  python main.py --no-summarize       # 跳过 AI 摘要
  python main.py --no-push           # 跳过推送
  python main.py --dry-run           # 只抓取不写入不推送
"""

import os
import sys
import io

# 修复 Windows GBK 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# 加载 .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import httpx
from sources import (
    HackerNewsSource,
    ArXivSource,
    GitHubTrendingSource,
    ProductHuntSource,
    RSSSource,
)
from summarizer import summarize_batch
from pusher import send_email, send_wechat


# ─── RSS 源的简配定义（外媒 + 中文媒体）────────────────────────

# 外媒 AI 博客
OPENAI_BLOG = "https://openai.com/news/rss.xml"
ANTHROPIC_BLOG = "https://rsshub.app/anthropic/blog"
GOOGLE_AI_BLOG = "https://blog.google/technology/ai/feeds/posts/default/?alt=rss"

# 中文 AI 媒体 (官方 RSS + RSSHub 备用)
JIQIZHIXIN_RSS = "https://rsshub.app/jiqizhixin/latest"
LIANGZIWEI_RSS = "https://rsshub.app/qbitai/latest"
_36KR_AI_RSS = "https://36kr.com/feed"


def create_rss_source(name: str, display: str, category: str, feeds: list[str]) -> RSSSource:
    """动态创建 RSS 源（无需为每个源单独写类）"""
    source = RSSSource()
    source.name = name
    source.display_name = display
    source.category = category
    source.feeds = feeds
    return source


# ─── 所有数据源列表 ─────────────────────────────────────────

def get_all_sources() -> list:
    return [
        HackerNewsSource(),
        ArXivSource(),
        GitHubTrendingSource(),
        ProductHuntSource(),
        create_rss_source("openai", "OpenAI Blog", "news", [OPENAI_BLOG]),
        create_rss_source("anthropic", "Anthropic Blog", "news", [ANTHROPIC_BLOG]),
        create_rss_source("googleai", "Google AI Blog", "news", [GOOGLE_AI_BLOG]),
        create_rss_source("jiqizhixin", "机器之心", "news", [JIQIZHIXIN_RSS]),
        create_rss_source("liangziwei", "量子位", "news", [LIANGZIWEI_RSS]),
        create_rss_source("36kr_ai", "36氪 AI", "news", [_36KR_AI_RSS]),
    ]


# ─── SQLite 操作（直接用 sqlite3，不依赖 Prisma） ────────────

DB_PATH = Path(__file__).parent.parent / "prisma" / "dev.db"


def normalize_datetime(dt_str: str) -> str:
    """将各种日期格式统一为 Prisma SQLite 兼容格式: YYYY-MM-DDTHH:MM:SS.000Z"""
    if not dt_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # 截取前 19 个字符 (YYYY-MM-DDTHH:MM:SS)，补 .000Z
    dt_str = dt_str.strip().replace(" ", "T")
    if len(dt_str) >= 19:
        dt_str = dt_str[:19]
    return dt_str + ".000Z"


def init_db():
    """确保表结构存在，使用 Prisma 兼容的 ISO 8601 格式"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Article (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            summary TEXT NOT NULL DEFAULT '',
            aiDigest TEXT,
            source TEXT NOT NULL,
            sourceName TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'news',
            publishedAt TEXT NOT NULL,
            fetchedAt TEXT NOT NULL,
            pushed INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def upsert_articles(articles: list[dict]) -> int:
    """写入文章，URL 去重，返回新插入数量。所有时间字段使用 ISO 8601 格式"""
    conn = sqlite3.connect(str(DB_PATH))
    new_count = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    for a in articles:
        # 生成安全的 ID（只保留字母数字和连字符）
        import re
        raw_id = f"{a['source']}-{a.get('published_at', '')[:10]}-{a['url'][:40]}"
        safe_id = re.sub(r"[^a-zA-Z0-9\-_]", "-", raw_id)[:100]

        published_at = a.get("published_at", now)
        # 统一为 Prisma 兼容的 ISO 8601 格式
        published_at = normalize_datetime(published_at)

        try:
            conn.execute(
                """INSERT OR IGNORE INTO Article
                   (id, title, url, summary, aiDigest, source, sourceName, category, publishedAt, fetchedAt, createdAt)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    safe_id,
                    a["title"],
                    a["url"],
                    a.get("summary", ""),
                    a.get("ai_digest"),
                    a["source"],
                    a.get("source_name", a["source"]),
                    a.get("category", "news"),
                    published_at,
                    now,
                    now,
                ),
            )
            if conn.total_changes > 0:
                new_count += 1
        except Exception as e:
            print(f"  [WARN] 写入失败: {a.get('title', '?')[:30]} — {e}")

    conn.commit()
    conn.close()
    return new_count


def rank_articles_for_push(articles: list[dict]) -> list[dict]:
    """按分类交错排列，让推送内容多样化：产品优先，论文/新闻/开源交替"""
    buckets: dict[str, list[dict]] = {"product": [], "paper": [], "news": [], "oss": []}
    for a in articles:
        cat = a.get("category", "news")
        if cat not in buckets:
            cat = "news"
        buckets[cat].append(a)

    result: list[dict] = []
    max_len = max(len(b) for b in buckets.values())
    # 优先级：product > news > paper > oss，交错取 2:2:1:1
    ratios = {"product": 2, "news": 2, "paper": 1, "oss": 1}
    indices = {k: 0 for k in buckets}

    while True:
        added = False
        for cat in ["product", "news", "paper", "oss"]:
            for _ in range(ratios.get(cat, 1)):
                idx = indices[cat]
                if idx < len(buckets[cat]):
                    result.append(buckets[cat][idx])
                    indices[cat] += 1
                    added = True
        if not added:
            break

    return result


# ─── 主流程 ─────────────────────────────────────────────────

async def main(summarize: bool = True, push: bool = True, dry_run: bool = False):
    print("=" * 50)
    print(f"  AI Radar 每日抓取 — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    # ── Step 1: 并发抓取所有数据源 ──
    print("\n📡 Step 1: 抓取数据源...")
    sources = get_all_sources()
    async with httpx.AsyncClient(timeout=30) as client:
        # 为每个 source 注入共享 httpx client
        for src in sources:
            if hasattr(src, "_client"):
                src._client = client

        # 并发执行所有 fetch
        tasks = [src.fetch() for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: list[dict] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  [ERROR] {sources[i].__class__.__name__}: {result}")
        elif isinstance(result, list):
            all_articles.extend(result)

    print(f"\n📊 总计抓取: {len(all_articles)} 条（去重前）")

    if not all_articles:
        print("⚠️  没有抓到任何文章，退出")
        return

    # ── Step 2: URL 去重 ──
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for a in all_articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique.append(a)
    print(f"📊 去重后: {len(unique)} 条")

    # ── Step 3: AI 摘要 ──
    if summarize:
        print("\n🤖 Step 2: AI 摘要生成...")
        # 先按分类交错排列，确保 AI 摘要覆盖多种类型
        unique = rank_articles_for_push(unique)
        unique = summarize_batch(unique)
    else:
        print("\n⏭️  跳过 AI 摘要 (--no-summarize)")

    # ── Step 4: 写入数据库 ──
    if not dry_run:
        init_db()
        new_count = upsert_articles(unique)
        print(f"\n💾 Step 3: 写入数据库 — 新增 {new_count} 条")
    else:
        print("\n🔍 Dry-run 模式，不写入数据库")
        # 打印前 10 条预览
        for i, a in enumerate(unique[:10]):
            print(f"  {i+1}. [{a['source_name']}] {a['title'][:60]}")
        return

    # ── Step 5: 推送 ──
    if push:
        print("\n📨 Step 4: 推送...")
        # 按分类交错排列，避免全部是同一类型
        ranked = rank_articles_for_push(unique)
        await send_email(ranked[:40])
        await send_wechat(ranked[:15])
    else:
        print("\n⏭️  跳过推送 (--no-push)")

    print("\n✅ AI Radar 抓取完成!")


if __name__ == "__main__":
    summarize = "--no-summarize" not in sys.argv
    push = "--no-push" not in sys.argv
    dry_run = "--dry-run" in sys.argv
    asyncio.run(main(summarize=summarize, push=push, dry_run=dry_run))
