"""AI 摘要生成器 — 调用 DeepSeek API 生成 AI PM 视角的中文解读"""

import os
from openai import OpenAI


# DeepSeek API 兼容 OpenAI SDK，只需改 base_url 和 api_key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def get_client() -> OpenAI:
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


SYSTEM_PROMPT = """你是一位资深的 AI 产品经理，帮助另一位 AI PM 实习生快速了解行业动态。

你的任务：根据文章标题和摘要，生成一段 100-150 字的中文解读，从以下维度分析：
1. **产品洞察**：这个技术/产品解决了什么用户问题？有什么产品设计亮点？
2. **行业影响**：对 AI 行业格局有什么影响？谁会受益、谁会被挑战？
3. **值得关注的原因**：为什么 AI PM 应该关注这条动态？

要求：
- 用简洁犀利的中文，不要废话套话
- 如果是论文，点出核心创新和可能的产品化方向
- 如果是产品发布，分析竞品格局和产品策略
- 如果是新闻，提炼对行业的信号意义
- 不要重复原文，要给出你自己的判断和洞察"""


def summarize_article(title: str, summary: str, source_name: str) -> str | None:
    """为单篇文章生成 AI PM 视角摘要，失败返回 None"""
    if not DEEPSEEK_API_KEY:
        print("  [SKIP] 未配置 DEEPSEEK_API_KEY，跳过 AI 摘要")
        return None

    client = get_client()

    user_prompt = f"""来源：{source_name}
标题：{title}
原文摘要：{summary[:800]}

请生成 AI PM 视角的中文解读（100-150字）："""

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=800,
            temperature=0.7,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"  [WARN] AI 摘要生成失败: {e}")
        return None


def summarize_batch(articles: list[dict], max_count: int = 50) -> list[dict]:
    """批量为文章生成 AI 摘要，优先处理摘要较短的文章（如 Product Hunt 等短文案源）"""
    if not DEEPSEEK_API_KEY:
        print("[AI摘要] 未配置 DEEPSEEK_API_KEY，跳过所有摘要")
        return articles

    # 筛选需要摘要的文章
    need_summary = [a for a in articles if not a.get("ai_digest")]

    # 优先给摘要短的文章生成 AI 解读（摘要越短越需要 AI 补充）
    need_summary.sort(key=lambda a: len(a.get("summary", "")))

    to_process = need_summary[:max_count]

    short_count = sum(1 for a in to_process if len(a.get("summary", "")) < 100)
    print(f"[AI摘要] 为 {len(to_process)}/{len(need_summary)} 篇文章生成摘要（其中 {short_count} 条原文摘要<100字，优先处理）...")

    for i, article in enumerate(to_process):
        digest = summarize_article(
            article["title"],
            article.get("summary", ""),
            article.get("source_name", ""),
        )
        article["ai_digest"] = digest
        if digest:
            print(f"  [{i+1}/{len(to_process)}] ✓ {article['title'][:40]}...")

    print(f"[AI摘要] 完成: {sum(1 for a in to_process if a.get('ai_digest'))} 条成功")
    return articles
