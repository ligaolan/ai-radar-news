# AI Radar 数据源适配器
# 每种数据源一个模块，统一返回 Article dict 列表

from .rss_base import RSSSource
from .hackernews import HackerNewsSource
from .arxiv import ArXivSource
from .github_trending import GitHubTrendingSource
from .producthunt import ProductHuntSource

__all__ = [
    "RSSSource",
    "HackerNewsSource",
    "ArXivSource",
    "GitHubTrendingSource",
    "ProductHuntSource",
]
