"""Hacker News AI 相关热门文章 — 通过 hnrss.org 获取"""

from .rss_base import RSSSource


class HackerNewsSource(RSSSource):
    name = "hackernews"
    display_name = "Hacker News"
    category = "news"

    # hnrss.org 提供过滤后的 RSS：AI 相关关键词，最近 50 条，评分 >= 10
    feeds = [
        "https://hnrss.org/frontpage?q=ai+OR+llm+OR+gpt+OR+claude+OR+openai+OR+anthropic+OR+deepseek+OR+gemini+OR+mistral+OR+stable+OR+diffusion+OR+transformer+OR+rag&points=10&count=20",
    ]
