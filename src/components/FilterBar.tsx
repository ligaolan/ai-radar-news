"use client";

import { useMemo } from "react";

interface Filters {
  category: string;
  source: string;
  date: string;
}

const CATEGORIES = [
  { value: "", label: "全部分类" },
  { value: "paper", label: "📄 论文" },
  { value: "product", label: "🚀 产品" },
  { value: "news", label: "📰 新闻" },
  { value: "oss", label: "💻 开源" },
];

const SOURCES = [
  { value: "", label: "全部来源" },
  { value: "hackernews", label: "Hacker News" },
  { value: "arxiv", label: "ArXiv" },
  { value: "github", label: "GitHub Trending" },
  { value: "producthunt", label: "Product Hunt" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "googleai", label: "Google AI" },
  { value: "jiqizhixin", label: "机器之心" },
  { value: "liangziwei", label: "量子位" },
  { value: "36kr_ai", label: "36氪 AI" },
];

interface FilterBarProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onPageReset: () => void;
}

export default function FilterBar({ filters, onChange, onPageReset }: FilterBarProps) {
  // 生成最近 30 天的日期选项
  const dateOptions = useMemo(() => {
    const opts = [{ value: "", label: "全部日期" }];
    for (let i = 0; i < 30; i++) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const val = d.toISOString().slice(0, 10);
      const label = i === 0 ? "今天" : i === 1 ? "昨天" : val;
      opts.push({ value: val, label });
    }
    return opts;
  }, []);

  const update = (key: keyof Filters, value: string) => {
    onChange({ ...filters, [key]: value });
    onPageReset();
  };

  const selectClass =
    "px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text)] focus:outline-none focus:border-[var(--color-accent)] transition-colors cursor-pointer";

  return (
    <div className="flex flex-wrap gap-3 mb-6">
      <select value={filters.category} onChange={(e) => update("category", e.target.value)} className={selectClass}>
        {CATEGORIES.map((c) => (
          <option key={c.value} value={c.value}>{c.label}</option>
        ))}
      </select>
      <select value={filters.source} onChange={(e) => update("source", e.target.value)} className={selectClass}>
        {SOURCES.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
      <select value={filters.date} onChange={(e) => update("date", e.target.value)} className={selectClass}>
        {dateOptions.map((d) => (
          <option key={d.value} value={d.value}>{d.label}</option>
        ))}
      </select>
    </div>
  );
}
