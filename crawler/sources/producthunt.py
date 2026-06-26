"""Product Hunt AI 产品 — 通过 RSS 获取"""

from .rss_base import RSSSource


class ProductHuntSource(RSSSource):
    name = "producthunt"
    display_name = "Product Hunt"
    category = "product"

    feeds = [
        "https://www.producthunt.com/feed?category=ai",
    ]
