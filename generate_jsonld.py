#!/usr/bin/env python3
"""实体主数据 → Organization JSON-LD 生成器

从一份 entity.yaml 生成各语言版本共用同一个 @id 的 Organization JSON-LD，
保证 legalName / brand / 地址 / 认证编号等事实字段在所有语言完全一致，
只有 description 随语言变化。

规则来自 https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party
用法:
  python generate_jsonld.py                          # 用 entity.yaml，输出到 output/
  python generate_jsonld.py --data my.yaml --out dir
"""
import argparse
import json
import os
import sys

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_org(data, lang=None):
    """Build one Organization JSON-LD dict from master data."""
    legal = data.get("legal", {}) or {}
    brand = data.get("brand", {}) or {}
    factory = data.get("factory", {}) or {}
    contact = data.get("contact", {}) or {}
    addr = legal.get("address", {}) or {}

    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": data.get("entity_id") or contact.get("website", ""),
        "name": brand.get("name") or legal.get("brand_name", ""),
        "legalName": legal.get("legal_name", ""),
        "url": contact.get("website", ""),
    }

    if legal.get("founded"):
        org["foundingDate"] = str(legal["founded"])
    if legal.get("vat_id"):
        org["vatID"] = legal["vat_id"]
    if legal.get("iso6523_code"):
        org["iso6523Code"] = legal["iso6523_code"]

    if addr:
        org["address"] = {
            "@type": "PostalAddress",
            "streetAddress": addr.get("street", ""),
            "addressLocality": addr.get("locality", ""),
            "addressRegion": addr.get("region", ""),
            "postalCode": addr.get("postal_code", ""),
            "addressCountry": addr.get("country", ""),
        }

    if brand.get("logo"):
        org["logo"] = brand["logo"]

    if contact.get("email"):
        org["email"] = contact["email"]
    if contact.get("phone"):
        org["telephone"] = contact["phone"]

    same_as = data.get("same_as") or []
    if same_as:
        org["sameAs"] = same_as

    # 语言描述：只有这一段随语言变化，事实字段不翻译
    langs = data.get("languages", {}) or {}
    if lang and lang in langs:
        desc = (langs[lang] or {}).get("description")
        if desc:
            org["description"] = desc

    # 工厂身份：作为额外事实写入（可选字段，注明非 schema.org 标准时用 alternateName 保留）
    if factory.get("is_manufacturer"):
        extra = []
        if factory.get("production_address"):
            extra.append("Factory: " + factory["production_address"])
        if factory.get("area"):
            extra.append("Factory area: " + factory["area"])
        if factory.get("production_lines"):
            extra.append("Production lines: " + str(factory["production_lines"]))
        if extra:
            org["disambiguatingDescription"] = "; ".join(extra)

    # 认证：用 hasCredential 表达（名称 + 编号）
    certs = data.get("certifications") or []
    creds = []
    for c in certs:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        cred = {
            "@type": "EducationalOccupationalCredential",
            "name": c["name"],
        }
        if c.get("number"):
            cred["identifier"] = c["number"]
        if c.get("issuer"):
            cred["recognizedBy"] = {"@type": "Organization", "name": c["issuer"]}
        creds.append(cred)
    if creds:
        org["hasCredential"] = creds

    return org


def main():
    ap = argparse.ArgumentParser(description="生成多语言一致的 Organization JSON-LD")
    ap.add_argument("--data", default="entity.yaml", help="主数据 YAML，默认 entity.yaml")
    ap.add_argument("--out", default="output", help="输出目录，默认 output/")
    args = ap.parse_args()

    if not os.path.exists(args.data):
        print(f"找不到 {args.data}。请复制 entity.example.yaml 为 entity.yaml 并填写。", file=sys.stderr)
        sys.exit(1)

    with open(args.data, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    os.makedirs(args.out, exist_ok=True)
    langs = list((data.get("languages") or {}).keys()) or ["default"]

    written = []
    for lang in langs:
        org = build_org(data, lang if lang != "default" else None)
        name = "organization.jsonld" if lang == "default" else f"organization-{lang}.jsonld"
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(org, ensure_ascii=False, indent=2) + "\n")
        written.append(path)

    # 校验：所有语言的 @id 必须一致
    ids = set()
    for p in written:
        with open(p, encoding="utf-8") as f:
            ids.add(json.load(f).get("@id"))
    if len(ids) != 1:
        print("[警告] 检测到多个 @id，实体会被拆成多家：", ids, file=sys.stderr)
    else:
        print(f"[通过] 所有 {len(langs)} 个语言版本共用同一个 @id: {next(iter(ids))}")

    print("已生成:")
    for p in written:
        print(" ", p)
    print("\n提醒：JSON-LD 里的事实必须同时出现在页面可见文字里。")
    print("原文: https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party")


if __name__ == "__main__":
    main()
