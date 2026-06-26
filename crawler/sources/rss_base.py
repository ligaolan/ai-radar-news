"""通用 RSS 抓取器基类"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional
import feedparser
import httpx


class RSSSource:
    """RSS 源基类，子类只需定义 name / display_name / category / feeds"""

    name: str = ""
    display_name: str = ""
    category: str = "news"  # paper / product / news / oss
    feeds: list[str] = []  # RSS URL 列表
    timeout: int = 30
    max_age_days: int = 3  # 只保留最近 N 天的文章

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client
        self._own_client = False
        self._cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=self.max_age_days)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AI-Radar/1.0; +https://github.com)",
                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
                },
            )
            self._own_client = True
        return self._client

    async def close(self):
        if self._own_client and self._client:
            await self._client.aclose()

    def _parse_entry(self, entry, feed_url: str) -> dict | None:
        """将 feedparser entry 转为标准 Article dict，子类可重写"""
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            return None

        # 摘要：优先用 content:encoded > summary > description
        summary = ""
        if "content" in entry and entry.content:
            summary = entry.content[0].get("value", "")
        if not summary:
            summary = entry.get("summary", "")
        if not summary:
            summary = entry.get("description", "")

        # 清理 HTML 标签
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        summary = summary[:500] if summary else ""

        # 发布时间
        published = datetime.now(timezone.utc).replace(tzinfo=None)
        if "published_parsed" in entry and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif "updated_parsed" in entry and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])

        # 过滤旧文
        if published < self._cutoff:
            return None

        return {
            "title": title,
            "url": link,
            "summary": summary,
            "source": self.name,
            "source_name": self.display_name,
            "category": self.category,
            "published_at": published.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }

    async def fetch(self) -> list[dict]:
        """抓取所有 RSS feed，返回 Article dict 列表"""
        client = await self._get_client()
        articles: list[dict] = []

        for feed_url in self.feeds:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

                for entry in feed.entries:
                    article = self._parse_entry(entry, feed_url)
                    if article:
                        articles.append(article)

            except Exception as e:
                print(f"  [WARN] {self.display_name} feed 抓取失败: {feed_url} — {e}")

        print(f"  [{self.display_name}] 抓到 {len(articles)} 条")
        return articles
