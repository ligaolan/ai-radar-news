"""GitHub AI 热门项目 — 通过 GitHub Search API 查询"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx


class GitHubTrendingSource:
    """搜索 GitHub 上最近创建的 AI 相关热门仓库"""

    name = "github"
    display_name = "GitHub Trending"
    category = "oss"
    timeout = 30

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client
        self._own_client = False

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "AI-Radar/1.0",
                    "Accept": "application/vnd.github+json",
                },
            )
            self._own_client = True
        return self._client

    async def close(self):
        if self._own_client and self._client:
            await self._client.aclose()

    async def fetch(self) -> list[dict]:
        """使用 GitHub Search API 查询 AI 相关热门仓库"""
        client = await self._get_client()
        articles: list[dict] = []
        seen_full_names: set[str] = set()

        # 搜索最近 7 天创建的 AI/LLM 相关仓库，按 stars 排序
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        query = f"ai OR llm OR agent OR rag created:>={seven_days_ago}"
        url = "https://api.github.com/search/repositories"

        try:
            resp = await client.get(
                url,
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 20,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            for repo in data.get("items", []):
                full_name = repo.get("full_name", "")
                if full_name in seen_full_names:
                    continue
                seen_full_names.add(full_name)

                desc = repo.get("description") or ""
                articles.append({
                    "title": full_name,
                    "url": repo.get("html_url", f"https://github.com/{full_name}"),
                    "summary": f"⭐ {repo.get('stargazers_count', 0)} | {desc[:400]}",
                    "source": self.name,
                    "source_name": self.display_name,
                    "category": self.category,
                    "published_at": repo.get("created_at", datetime.now(timezone.utc).isoformat()),
                })

        except Exception as e:
            print(f"  [WARN] GitHub Search API 失败: {e}")

        print(f"  [GitHub Trending] 抓到 {len(articles)} 条")
        return articles
