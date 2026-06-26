import { prisma } from "@/lib/prisma";
import { NextRequest, NextResponse } from "next/server";

// GET /api/articles?category=paper&source=hackernews&date=2026-06-25&page=1
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const source = searchParams.get("source");
  const date = searchParams.get("date");
  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 20;

  const where: Record<string, unknown> = {};
  if (category) where.category = category;
  if (source) where.source = source;
  if (date) {
    const start = new Date(date);
    const end = new Date(date);
    end.setDate(end.getDate() + 1);
    where.publishedAt = { gte: start, lt: end };
  }

  const [articles, total] = await Promise.all([
    prisma.article.findMany({
      where,
      orderBy: { publishedAt: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
    }),
    prisma.article.count({ where }),
  ]);

  return NextResponse.json({
    articles,
    total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
  });
}
