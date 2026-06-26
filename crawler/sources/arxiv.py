"""ArXiv 最新 AI 论文 — 通过 arXiv API 获取"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
import feedparser


class ArXivSource:
    """arXiv API 抓取，搜索 cs.AI 和 cs.CL 分类的新论文"""

    name = "arxiv"
    display_name = "ArXiv"
    category = "paper"
    timeout = 30

    # arXiv API 搜索端点
    base_url = "https://export.arxiv.org/api/query"

    # 搜索关键词：AI 相关
    queries = [
        'cat:cs.AI',
        'cat:cs.CL',
        'all:"large language model"',
        'all:"AI agent"',
    ]

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client
        self._own_client = False

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "AI-Radar/1.0"},
            )
            self._own_client = True
        return self._client

    async def close(self):
        if self._own_client and self._client:
            await self._client.aclose()

    def _build_url(self, query: str, max_results: int = 10) -> str:
        """构建 arXiv API URL"""
        # 搜索最近 3 天的论文，按提交时间排序
        return (
            f"{self.base_url}?search_query={query}"
            f"&start=0&max_results={max_results}"
            f"&sortBy=submittedDate&sortOrder=descending"
        )

    def _parse_entry(self, entry) -> dict | None:
        """将 arXiv API entry 转为标准 Article dict"""
        title = entry.get("title", "").strip().replace("\n", " ")
        link = entry.get("link", "")
        if not title or not link:
            return None

        summary = entry.get("summary", "")
        # 清理 HTML
        import re
        summary = re.sub(r"<[^>]+>", " ", summary).strip()
        summary = summary[:500] if summary else ""

        published = datetime.now(timezone.utc).replace(tzinfo=None)
        if "published" in entry:
            try:
                published = datetime.strptime(entry["published"], "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                pass

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
        """抓取 arXiv 论文"""
        client = await self._get_client()
        articles: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.queries:
            try:
                url = self._build_url(query)
                resp = await client.get(url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

                for entry in feed.entries:
                    article = self._parse_entry(entry)
                    if article and article["url"] not in seen_urls:
                        seen_urls.add(article["url"])
                        articles.append(article)

                # arXiv API 有频率限制，间隔一下
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"  [WARN] ArXiv query 失败: {query} — {e}")

        print(f"  [ArXiv] 抓到 {len(articles)} 条")
        return articles
