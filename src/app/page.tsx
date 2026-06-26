"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import FilterBar from "@/components/FilterBar";
import Timeline from "@/components/Timeline";

interface Article {
  id: string;
  title: string;
  url: string;
  summary: string;
  aiDigest: string | null;
  source: string;
  sourceName: string;
  category: string;
  publishedAt: string;
}

interface Filters {
  category: string;
  source: string;
  date: string;
}

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [filters, setFilters] = useState<Filters>({ category: "", source: "", date: "" });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const retryRef = useRef(0);

  const fetchArticles = useCallback(async (f: Filters, p: number) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (f.category) params.set("category", f.category);
      if (f.source) params.set("source", f.source);
      if (f.date) params.set("date", f.date);
      params.set("page", String(p));

      const res = await fetch(`/api/articles?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setArticles(data.articles);
      setTotalPages(data.totalPages);
      retryRef.current = 0;
    } catch (err) {
      console.error("获取文章失败:", err);
      // Prisma 可能尚未初始化，自动重试 3 次
      if (retryRef.current < 3) {
        retryRef.current++;
        setTimeout(() => fetchArticles(f, p), 2000);
      } else {
        setError("无法连接数据库，请确保已运行 prisma db push");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchArticles(filters, page);
  }, [filters, page, fetchArticles]);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          <span className="text-[var(--color-accent)]">AI</span> Radar
        </h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          AI 行业每日动态 · AI PM 视角智能解读
        </p>
      </header>

      {/* Filter */}
      <FilterBar filters={filters} onChange={setFilters} onPageReset={() => setPage(1)} />

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-8 w-8 border-2 border-[var(--color-accent)] border-t-transparent rounded-full" />
        </div>
      ) : error ? (
        <div className="text-center py-20 text-[var(--color-text-muted)]">
          <p>{error}</p>
          <button onClick={() => fetchArticles(filters, page)} className="mt-4 text-[var(--color-accent)] hover:underline">
            重试
          </button>
        </div>
      ) : articles.length === 0 ? (
        <div className="text-center py-20 text-[var(--color-text-muted)]">
          <p className="text-5xl mb-4">📡</p>
          <p className="text-lg">暂无数据</p>
          <p className="text-sm mt-2">运行 crawler 抓取第一批 AI 动态</p>
        </div>
      ) : (
        <>
          <Timeline articles={articles} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-lg border border-[var(--color-border)] disabled:opacity-30 hover:bg-[var(--color-surface)] transition-colors"
              >
                ← 上一页
              </button>
              <span className="px-4 py-2 text-[var(--color-text-muted)]">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 rounded-lg border border-[var(--color-border)] disabled:opacity-30 hover:bg-[var(--color-surface)] transition-colors"
              >
                下一页 →
              </button>
            </div>
          )}
        </>
      )}
    </main>
  );
}
