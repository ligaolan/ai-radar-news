import ArticleCard from "./ArticleCard";

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

// 按日期分组
function groupByDate(articles: Article[]): Map<string, Article[]> {
  const groups = new Map<string, Article[]>();
  for (const a of articles) {
    const date = new Date(a.publishedAt).toISOString().slice(0, 10);
    const list = groups.get(date) || [];
    list.push(a);
    groups.set(date, list);
  }
  return groups;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);

  if (dateStr === today) return "今天";
  if (dateStr === yesterday) return "昨天";
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

export default function Timeline({ articles }: { articles: Article[] }) {
  const groups = groupByDate(articles);

  return (
    <div className="space-y-8">
      {Array.from(groups.entries()).map(([date, items]) => (
        <section key={date}>
          <h2 className="text-sm font-semibold text-[var(--color-accent)] mb-4 uppercase tracking-wider">
            {formatDate(date)}
            <span className="ml-2 text-[var(--color-text-muted)] font-normal normal-case">
              ({items.length} 条)
            </span>
          </h2>
          <div className="space-y-3">
            {items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
