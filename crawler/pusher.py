"""推送模块 — 邮件（Resend） + 企业微信机器人"""

import os
import json
import httpx

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "ai-radar@example.com")
RESEND_TO = os.getenv("RESEND_TO", "")
WECHAT_WEBHOOK_URL = os.getenv("WECHAT_WEBHOOK_URL", "")

CATEGORY_ICON = {
    "paper": "📄",
    "product": "🚀",
    "news": "📰",
    "oss": "💻",
}


def build_email_html(articles: list[dict]) -> str:
    """构建邮件 HTML"""
    by_category: dict[str, list[dict]] = {}
    for a in articles:
        cat = a.get("category", "news")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(a)

    sections = ""
    for cat, items in by_category.items():
        icon = CATEGORY_ICON.get(cat, "📌")
        sections += f'<h2 style="color:#6c8cff;margin-top:24px;">{icon} {cat.upper()} ({len(items)})</h2>\n'
        for a in items:
            digest_html = ""
            if a.get("ai_digest"):
                digest_html = f"""
                <div style="margin-top:8px;padding:12px;background:#1a1d2e;border-left:3px solid #6c8cff;border-radius:4px;">
                  <p style="margin:0;font-size:13px;color:#a0a4b8;">🤖 AI PM 视角</p>
                  <p style="margin:4px 0 0;font-size:14px;color:#e4e6f0;">{a['ai_digest']}</p>
                </div>"""
            sections += f"""
            <div style="margin-bottom:16px;padding:16px;background:#1a1d2e;border-radius:8px;">
              <a href="{a['url']}" style="font-size:16px;color:#e4e6f0;text-decoration:none;font-weight:600;">
                {a['title']}
              </a>
              <p style="margin:4px 0;font-size:12px;color:#8b8fa8;">
                {a['source_name']} · {a.get('published_at', '')[:10]}
              </p>
              <p style="margin:8px 0 0;font-size:14px;color:#a0a4b8;">{a.get('summary', '')[:300]}</p>
              {digest_html}
            </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#0f1117;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <div style="max-width:640px;margin:0 auto;">
    <h1 style="color:#e4e6f0;font-size:24px;">
      <span style="color:#6c8cff;">AI</span> Radar 每日动态
    </h1>
    <p style="color:#8b8fa8;font-size:14px;">AI 行业最新动态 · AI PM 视角解读</p>
    {sections}
    <hr style="border-color:#2a2d3e;margin:24px 0;">
    <p style="color:#4a4d5e;font-size:12px;text-align:center;">
      AI Radar · 每日自动生成 · <a href="https://github.com" style="color:#6c8cff;">GitHub</a>
    </p>
  </div>
</body>
</html>"""


async def send_email(articles: list[dict]) -> bool:
    """通过 Resend API 发送邮件"""
    if not RESEND_API_KEY or not RESEND_TO:
        print("[推送] 未配置 RESEND_API_KEY 或 RESEND_TO，跳过邮件推送")
        return False

    html = build_email_html(articles)
    today = __import__("datetime").date.today().isoformat()

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"AI Radar <{RESEND_FROM}>",
                    "to": [RESEND_TO],
                    "subject": f"🤖 AI Radar 每日动态 — {today}",
                    "html": html,
                },
            )
            if resp.status_code == 200:
                print(f"[推送] 邮件发送成功 → {RESEND_TO}")
                return True
            else:
                print(f"[推送] 邮件发送失败: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            print(f"[推送] 邮件发送异常: {e}")
            return False


async def send_wechat(articles: list[dict], top_n: int = 10) -> bool:
    """通过企业微信机器人 Webhook 推送 Top N"""
    if not WECHAT_WEBHOOK_URL:
        print("[推送] 未配置 WECHAT_WEBHOOK_URL，跳过企微推送")
        return False

    today = __import__("datetime").date.today().isoformat()

    # 按分类优先级排序：product > paper > news > oss
    priority = {"product": 0, "paper": 1, "news": 2, "oss": 3}
    sorted_articles = sorted(articles, key=lambda a: priority.get(a.get("category"), 9))
    top = sorted_articles[:top_n]

    # 构建 Markdown 消息
    lines = [f"## 🤖 AI Radar 每日动态 ({today})\n"]
    for i, a in enumerate(top):
        icon = CATEGORY_ICON.get(a.get("category", "news"), "📌")
        lines.append(f"{i+1}. {icon} [{a['title']}]({a['url']}) — *{a['source_name']}*")
        if a.get("ai_digest"):
            lines.append(f"   > {a['ai_digest'][:100]}...")
        lines.append("")

    lines.append(f"\n> 共 {len(articles)} 条动态，查看全文请访问 [AI Radar Dashboard]")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                WECHAT_WEBHOOK_URL,
                json={
                    "msgtype": "markdown",
                    "markdown": {"content": "\n".join(lines)},
                },
            )
            if resp.status_code == 200 and resp.json().get("errcode") == 0:
                print(f"[推送] 企微消息发送成功 (Top {top_n})")
                return True
            else:
                print(f"[推送] 企微发送失败: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            print(f"[推送] 企微发送异常: {e}")
            return False
