# B2B GEO 实体一致性工具包

> AI 把工厂说成贸易公司、把两个品牌当成一家、搞错产地和认证——根源往往是实体信息不一致。这个工具包把「[B2B GEO 实体一致性](https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party)」的方法论做成一份主数据表 + 两个脚本，让你的企业身份在官网、结构化数据、各语言版本、第三方平台上只有一个答案。

**原文（完整方法与作者）**：[SEO小平 · seogeo.cc — B2B GEO实体一致性：品牌名、工厂身份与第三方背书怎么对齐](https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party)

**作者站点**：[seogeo.cc — 外贸 SEO / GEO 实战](https://seogeo.cc)

---

## 这是什么

实体一致性就是让「你是谁」在所有地方只有一个答案：**法定名、品牌、工厂身份、资质、联系方式**五层对齐，站内先写清，站外逐步修正。

在 GEO 时代，AI 靠「别人怎么提你」来认识你（Ahrefs 对 7.5 万品牌的研究：AI Overviews 品牌出现与全网品牌提及量相关性最高 0.664，外链数只有 0.218——相关不等于因果，但说明 AI 靠站外信号交叉验证）。如果别人提到的是五个不同名字，这些提及就无法累积到同一个实体上。

这个仓库把文章里可落地部分做成工具：

| 文件 | 作用 |
|------|------|
| [`entity.example.yaml`](entity.example.yaml) | 五层身份的**唯一主数据表**（法定主体/品牌/工厂/认证/联系方式/sameAs/多语言），复制成 `entity.yaml` 填你自己的 |
| [`generate_jsonld.py`](generate_jsonld.py) | 从主数据生成各语言共用一个 `@id` 的 Organization JSON-LD，事实字段完全一致，只有描述随语言变 |
| [`check_entity.py`](check_entity.py) | 抓官网核对：@id 是否唯一、JSON-LD 事实是否真的写在可见文字里、sameAs 是否混入第三方文章、品牌名/法定名是否出现 |
| [`docs/`](docs/) | 五层身份表、症状→排查对照表、站外盘点模板、多语言规则（这部分写成文档比代码合适） |

---

## 安装

Python 3.8+：

```bash
pip install -r requirements.txt
```

---

## 用法

### 第一步：填主数据表

```bash
cp entity.example.yaml entity.yaml
# 编辑 entity.yaml，把五层身份换成你自己的真实信息
```

关键规则（来自原文）：

- `legalName`（营业执照英文名）与 `name`（品牌名）分开写，不必改名，但要写清关系。
- `entity_id` 全站全语言只有一个，产品页的 brand/manufacturer 引用它，不要每页重写。
- `sameAs` 只放官方账号（LinkedIn 公司页、YouTube 频道、平台旗舰店），不放转载和第三方文章。
- `certifications` 只写能被发证机构官网查到的真实记录，过期证书不要放进结构化数据。
- `languages` 里品牌名/法定名/地址/认证编号保持原样，只翻译描述性文字。

### 第二步：生成 JSON-LD

```bash
python generate_jsonld.py
# 输出 output/organization.jsonld 及各语言 organization-<lang>.jsonld
```

脚本会自动校验所有语言版本的 `@id` 是否一致——不一致会报警，因为那意味着 AI 会把你拆成多家公司。把生成的 JSON-LD 贴到官网首页/About 页的 `<head>`。

### 第三步：核对线上一致性

```bash
python check_entity.py https://你的域名 --data entity.yaml --out report.md
```

报告会逐页检查 @id 唯一性、品牌名/法定名/认证是否出现在可见文字、sameAs 是否混入第三方链接。**JSON-LD 里写的事实必须同时出现在页面可见文字里**——否则违反 Google 结构化数据指南，AI 引用也无法核实。

---

## 站外对齐（工具管不到，但要人工做）

工具只能管站内。站外是工作量最大的部分，按原文的流程：

1. **盘点**：用中英文品牌名、法定名、旧名、常见拼错分别搜 Google 和 Bing，并在 AI 产品里问「Who is [品牌]」「Is [品牌] a manufacturer or trader」，把每个来源记入表格（模板见 [`docs/offsite-audit-template.md`](docs/offsite-audit-template.md)）。
2. **分类**：自己可控的 / 可申请修改的 / 不可控的。
3. **修正可控部分**：统一名称、地址、描述；过期证书下架；旧域名 301 到新域名。
4. **申请修改**：给展会主办方、协会、媒体发更正请求，附营业执照或证书扫描件。
5. **稀释旧信息**：不可控的旧信息无法删除时，用新的、一致的第三方提及让正确信息占多数。

完整排查表见 [`docs/identity-layers.md`](docs/identity-layers.md)。

---

## 多语言站点额外规则

如果网站有德语、西语、阿语等版本：

1. 品牌名和法定名在所有语言版本中**保持原样**，不做意译或音译，只翻译描述性文字。
2. 各语言版本的 About 页使用同一个 Organization `@id`，地址、认证编号、成立年份等事实字段完全相同，只有说明文字随语言变化。

本工具的 `generate_jsonld.py` 已把这两条做成自动校验。曾有人把西语站公司名意译成当地语言，结果在西语问题里 AI 把它当成了另一家本地经销商。

---

## 三个仓库是一条线

- [建站 SOP](https://github.com/suikusales-hub/ai-agent-b2b-static-site-sop) —— 怎么建
- [隐患体检工具](https://github.com/suikusales-hub/ai-built-site-seo-check) —— 建完怎么查收录/结构/GEO
- **本仓库** —— 查完怎么让「你是谁」全站全平台只有一个答案

---

## License

MIT —— 脚本代码可自由使用修改。五层身份框架与排查逻辑整理自 [seogeo.cc 原文](https://seogeo.cc/b2b-geo-entity-consistency-brand-factory-third-party)，原文著作权归作者 SEO小平 所有，转载请保留原文链接。
