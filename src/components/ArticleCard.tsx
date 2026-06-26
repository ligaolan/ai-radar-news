"use client";

import { useState } from "react";

interface Article {
  title: string;
  url: string;
  summary: string;
  aiDigest: string | null;
  source: string;
  sourceName: string;
  category: string;
  publishedAt: string;
}

const CATEGORY_MAP: Record<string, string> = {
  paper: "📄 论文",
  product: "🚀 产品",
  news: "📰 新闻",
  oss: "💻 开源",
};

export default function ArticleCard({ article }: { article: Article }) {
  const [expanded, setExpanded] = useState(false);

  const time = new Date(article.publishedAt).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <article
      className="group p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-accent)]/30 transition-all cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-base font-medium hover:text-[var(--color-accent)] transition-colors line-clamp-2"
          >
            {article.title}
          </a>
          <div className="flex items-center gap-2 mt-2 text-xs text-[var(--color-text-muted)]">
            <span className="font-medium text-[var(--color-accent)]">{article.sourceName}</span>
            <span>·</span>
            <span>{CATEGORY_MAP[article.category] || article.category}</span>
            <span>·</span>
            <time>{time}</time>
          </div>
        </div>
        <span className="text-xs text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-1">
          {expanded ? "收起 ▲" : "展开 ▼"}
        </span>
      </div>

      {/* 原文摘要 */}
      <p className="mt-2 text-sm text-[var(--color-text-muted)] line-clamp-2">{article.summary}</p>

      {/* AI 解读 - 展开时显示 */}
      {expanded && article.aiDigest && (
        <div className="mt-3 p-3 rounded-lg bg-[var(--color-accent-glow)] border border-[var(--color-accent)]/20">
          <p className="text-xs font-semibold text-[var(--color-accent)] mb-1">🤖 AI PM 视角解读</p>
          <p className="text-sm text-[var(--color-text)] leading-relaxed">{article.aiDigest}</p>
        </div>
      )}
    </article>
  );
}
