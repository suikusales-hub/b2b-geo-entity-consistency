# 多语言站点的实体一致性规则

> 来自 [seogeo.cc 原文第三节](https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party)。

## 两条硬规则

1. **品牌名和法定名在所有语言版本中保持原样**，不做意译或音译，只翻译描述性文字；否则 AI 在不同语言的检索结果里会看到不同的名字。
2. **各语言版本的 About 页使用同一个 Organization `@id`**，地址、认证编号、成立年份等事实字段完全相同，只有说明文字随语言变化。

真实教训：曾有客户把西语站的公司名意译成当地语言，结果在西语问题里 AI 把它当成了另一家本地经销商。语言版本越多，越需要一份主数据表来约束这些字段，并在每次新增语言时逐项核对一遍。

## Organization 结构化数据可用字段

Google 的 Organization 结构化数据文档给出的可用字段：

| 字段 | 说明 |
|------|------|
| `legalName` | 法定名称 |
| `vatID` | VAT 号 |
| `iso6523Code` | 如 DUNS 等标识（格式 `1234:XXXX`） |
| `address` | 地址 |
| `logo` | 至少 112×112 像素 |
| `sameAs` | 指向官方社交主页等 |

建议放在首页或关于页面。

## 实施清单（站内）

1. **About 页可见文字先写清楚**：法定名称、品牌名、两者关系、地址、成立年份、核心产品线、认证列表（名称、编号、机构、范围）。
2. **结构化数据与可见文字一致**：Google 通用指南要求只标注页面可见的内容，且必须真实代表页面。不要在 JSON-LD 里写页面上没有的认证或奖项。
3. **sameAs 只放官方账号**：LinkedIn 公司页、YouTube 频道、平台旗舰店等，不放转载或第三方文章。
4. **全站一个 Organization `@id`**：产品页的 brand、manufacturer 引用这个 `@id`，而不是每页重新写一份。

本工具包的 `generate_jsonld.py` 已把「同一 @id、事实字段跨语言一致」做成自动校验——见根目录 README。

原文：[https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party](https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party)
