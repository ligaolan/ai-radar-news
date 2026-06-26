import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Radar — AI 每日动态",
  description: "AI 行业最新动态抓取与智能摘要，AI PM 视角解读",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
