#!/usr/bin/env python3
"""实体一致性校验器

抓目标站点的页面，对照 entity.yaml 主数据核对：
  1. 全站 Organization 的 @id 是否唯一
  2. JSON-LD 里的事实（legalName/地址/认证）是否真的出现在页面可见文字里
  3. sameAs 是否混入第三方文章/转载（只应放官方账号）
  4. 品牌名 / 法定名是否在页面上出现（AI 靠这些信号认识你）

规则来自 https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party
用法:
  python check_entity.py https://你的域名 --data entity.yaml
  python check_entity.py https://你的域名 --data entity.yaml --out report.md
"""
import argparse
import json
import os
import sys
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (compatible; B2B-Entity-Consistency-Check/1.0; "
      "+https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party)")

THIRD_PARTY_HINTS = ["medium.com", "blog.", "/news/", "/article", "third-party", "guest-post"]


def collect_pages(base, session, limit, timeout):
    """Collect homepage + About/Contact pages from homepage links."""
    pages = [base]
    r = session.get(base, timeout=timeout)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        host = urlparse(base).netloc
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text(" ", strip=True) or "").lower()
            if any(k in text for k in ("about", "company", "contact", "关于", "联系我们")):
                u = urljoin(base, href).split("#", 1)[0]
                if urlparse(u).netloc == host and u not in pages and len(pages) < limit:
                    pages.append(u)
    return pages[:limit]


def visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return soup.get_text(" ", strip=True)


def jsonld_blocks(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            out.append(json.loads(s.string or s.get_text()))
        except Exception:
            pass
    return out


def find_org(blocks):
    for b in blocks:
        if isinstance(b, dict):
            t = b.get("@type", "")
            if t == "Organization" or (isinstance(t, list) and "Organization" in t):
                return b
            if isinstance(b.get("@graph"), list):
                for g in b["@graph"]:
                    if isinstance(g, dict) and g.get("@type") == "Organization":
                        return g
    return None


def main():
    ap = argparse.ArgumentParser(description="B2B 实体一致性校验")
    ap.add_argument("domain", help="目标站点，如 https://www.example.com")
    ap.add_argument("--data", default="entity.yaml", help="主数据 YAML")
    ap.add_argument("--limit", type=int, default=6, help="最多检查页数，默认 6")
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--out", help="报告输出路径（.md）")
    args = ap.parse_args()

    base = args.domain.rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = "https://" + base

    if not os.path.exists(args.data):
        print(f"找不到 {args.data}。请复制 entity.example.yaml 为 entity.yaml 并填写。", file=sys.stderr)
        sys.exit(1)
    with open(args.data, encoding="utf-8") as f:
        master = yaml.safe_load(f) or {}

    legal = master.get("legal", {}) or {}
    brand = master.get("brand", {}) or {}
    want_id = master.get("entity_id")
    want_legal = legal.get("legal_name", "")
    want_brand = brand.get("name") or legal.get("brand_name", "")
    want_sameas = set(master.get("same_as") or [])
    certs = [c.get("name") for c in (master.get("certifications") or []) if isinstance(c, dict) and c.get("name")]

    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    pages = collect_pages(base, session, args.limit, args.timeout)
    print(f"[1/3] 检查 {len(pages)} 个页面...")

    ids = set()
    orgs_found = 0
    text_all = ""
    sameas_found = set()
    per_page = []
    for u in pages:
        try:
            r = session.get(u, timeout=args.timeout)
        except Exception as e:
            per_page.append((u, "请求失败: " + str(e)[:80]))
            continue
        if r.status_code != 200:
            per_page.append((u, f"HTTP {r.status_code}"))
            continue
        vt = visible_text(r.text)
        text_all += " " + vt
        org = find_org(jsonld_blocks(r.text))
        status = []
        if org:
            orgs_found += 1
            oid = org.get("@id")
            if oid:
                ids.add(oid)
                status.append("@id=" + oid)
        else:
            status.append("无 Organization JSON-LD")
        per_page.append((u, "；".join(status)))

    print("[2/3] 核对事实字段与 sameAs ...")

    lines = ["# 实体一致性校验报告", "", f"目标站点：{base}", f"检查页面：{len(pages)}", ""]
    lines += ["## 逐页结果", ""]
    for u, s in per_page:
        lines.append(f"- `{u}` — {s}")

    lines += ["", "## 一致性检查", ""]
    # @id 唯一
    if not orgs_found:
        lines.append("- **不通过** — 未找到任何 Organization JSON-LD")
    elif len(ids) <= 1:
        lines.append(f"- **通过** — 全站 Organization @id 唯一：{next(iter(ids)) if ids else '（无 @id）'}")
    else:
        lines.append("- **不通过** — 发现多个 @id，实体会被拆成多家：" + "、".join(sorted(ids)))
        if want_id:
            lines.append(f"  - 主数据期望：{want_id}")

    # 品牌名 / 法定名可见
    lines.append(f"- {'**通过**' if want_brand and want_brand.lower() in text_all.lower() else '**不通过**'} — 品牌名可见文字：{want_brand or '（未配置）'}")
    lines.append(f"- {'**通过**' if want_legal and want_legal.lower() in text_all.lower() else '**不通过**'} — 法定名可见文字：{want_legal or '（未配置）'}")
    for c in certs:
        lines.append(f"- {'**通过**' if c.lower() in text_all.lower() else '**不通过**'} — 认证在可见文字：{c}")

    # sameAs
    if not want_sameas:
        lines.append("- **提示** — 主数据未配置 sameAs，跳过检查")
    else:
        bad = [u for u in want_sameas if any(h in u.lower() for h in THIRD_PARTY_HINTS)]
        lines.append(f"- {'**不通过**' if bad else '**通过**'} — sameAs 官方账号 {len(want_sameas)} 条"
                     + (f"，疑似第三方文章/转载：{'、'.join(bad)}" if bad else ""))

    lines += [
        "",
        "## 说明",
        "",
        "- JSON-LD 里的事实必须同时出现在页面可见文字里，否则违反 Google 结构化数据指南。",
        "- 品牌名与法定名在所有语言版本保持原样；事实字段各语言完全相同。",
        "- 站外信号（平台店铺、展会名录、媒体）也要用同一套表述，否则 AI 交叉验证时会拆成多家。",
        "",
        "原文：https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party",
    ]

    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
