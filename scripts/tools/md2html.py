#!/usr/bin/env python3
"""把带 mermaid 代码块的 Markdown 文档转成自包含 HTML（project-docs 工程视图文档用）。

- mermaid 代码块用本机 mmdc（mermaid-cli）预渲染成 SVG 并内嵌，离线可看
- 支持：frontmatter 剥离、标题、段落、有序/无序列表、表格、引用、代码块、粗体、行内代码、链接、【模型:xx】【表:xx】【存储:xx】【队列:xx】徽章
- 用法：python3 scripts/tools/md2html.py 输入.md 输出.html
"""
import html
import json
import os
import re
import subprocess
import sys
import tempfile

MERMAID_CONFIG = {
    "theme": "base",
    "themeVariables": {
        "fontFamily": "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Helvetica Neue, Arial, sans-serif",
        "fontSize": "14px",
        "primaryColor": "#f8fafc",
        "primaryBorderColor": "#94a3b8",
        "primaryTextColor": "#0f172a",
        "lineColor": "#475569",
        "clusterBkg": "#f8fafc",
        "clusterBorder": "#cbd5e1",
        "edgeLabelBackground": "#ffffff",
    },
    "flowchart": {"htmlLabels": True, "curve": "basis", "padding": 12, "nodeSpacing": 40, "rankSpacing": 50},
    "sequence": {"useMaxWidth": True},
}

CSS = r"""
:root{--bg:#ffffff;--fg:#0f172a;--muted:#475569;--line:#e2e8f0;--accent:#0f766e;--code:#f1f5f9;
--model:#fde68a;--model-b:#b45309;--db:#bfdbfe;--db-b:#1d4ed8;--store:#bbf7d0;--store-b:#15803d;--queue:#e9d5ff;--queue-b:#7e22ce;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 "PingFang SC","Hiragino Sans GB","Microsoft YaHei","Helvetica Neue",Arial,sans-serif}
.layout{display:grid;grid-template-columns:260px minmax(0,1fr);min-height:100vh}
nav.toc{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid var(--line);padding:20px 16px;background:#f8fafc;font-size:13px}
nav.toc h2{font-size:13px;margin:0 0 10px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
nav.toc a{display:block;color:var(--fg);text-decoration:none;padding:3px 0 3px 0;border-left:2px solid transparent}
nav.toc a.l2{padding-left:8px}
nav.toc a.l3{padding-left:22px;color:var(--muted)}
nav.toc a:hover{color:var(--accent)}
main{padding:32px 48px 80px;max-width:1180px}
h1{font-size:28px;margin:0 0 8px;line-height:1.3}
h2{font-size:21px;margin:40px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:17px;margin:28px 0 8px}
h4{font-size:15px;margin:20px 0 6px;color:var(--muted)}
p{margin:8px 0}
a{color:var(--accent)}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.92em;font-family:"JetBrains Mono","SF Mono",Menlo,Consolas,monospace}
pre{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:8px;overflow:auto;font-size:13px;line-height:1.55}
pre code{background:transparent;color:inherit;padding:0}
blockquote{margin:12px 0;padding:10px 16px;border-left:4px solid var(--accent);background:#f0fdfa;color:#134e4a;border-radius:0 6px 6px 0}
table{border-collapse:collapse;width:100%;margin:12px 0 18px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:7px 10px;vertical-align:top;text-align:left}
th{background:#f1f5f9;font-weight:600;position:sticky;top:0}
tr:nth-child(even) td{background:#fafafa}
ul,ol{padding-left:24px;margin:6px 0}
li{margin:3px 0}
figure.diagram{margin:16px 0 24px;padding:14px;border:1px solid var(--line);border-radius:10px;background:#fff;overflow:auto}
figure.diagram svg{height:auto;display:block;margin:0 auto}
figure.diagram.fit svg{width:100%!important}
figure.diagram .bar{display:flex;justify-content:flex-end;gap:8px;margin-bottom:6px}
figure.diagram .bar button{font:12px inherit;padding:2px 10px;border:1px solid #cbd5e1;border-radius:6px;background:#f8fafc;cursor:pointer}
figure.diagram .bar button:hover{background:#e2e8f0}
figure.diagram details{margin-top:10px;font-size:12px;color:var(--muted)}
figure.diagram details pre{margin-top:8px;font-size:12px}
.meta{color:var(--muted);font-size:13px;margin-bottom:24px}
.legend{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px;font-size:13px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{display:inline-block;width:14px;height:14px;border-radius:3px;border:1px solid}
.tag{display:inline-block;padding:0 6px;border-radius:4px;font-size:12px;border:1px solid;white-space:nowrap}
.tag.model{background:var(--model);border-color:var(--model-b)}
.tag.db{background:var(--db);border-color:var(--db-b)}
.tag.store{background:var(--store);border-color:var(--store-b)}
.tag.queue{background:var(--queue);border-color:var(--queue-b)}
@media (max-width:900px){.layout{grid-template-columns:1fr}nav.toc{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}main{padding:20px 16px}}
@media print{nav.toc{display:none}.layout{grid-template-columns:1fr}}
"""

TAG_MAP = {"模型": "model", "表": "db", "存储": "store", "队列": "queue"}


def slugify(text, used):
    base = re.sub(r"[^\w一-鿿-]+", "-", text.strip()).strip("-").lower() or "sec"
    slug, n = base, 1
    while slug in used:
        n += 1
        slug = f"{base}-{n}"
    used.add(slug)
    return slug


def inline(text):
    """行内语法：代码、粗体、链接、标签徽章 【模型:xxx】。"""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
            continue
        s = html.escape(p)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"【(模型|表|存储|队列)[:：]([^】]+)】",
                   lambda m: f'<span class="tag {TAG_MAP[m.group(1)]}">{m.group(2)}</span>', s)
        s = s.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
        out.append(s)
    return "".join(out)


def render_mermaid(src, idx, tmpdir):
    mmd = os.path.join(tmpdir, f"d{idx}.mmd")
    svg = os.path.join(tmpdir, f"d{idx}.svg")
    cfg = os.path.join(tmpdir, "mermaid.json")
    with open(cfg, "w", encoding="utf-8") as f:
        json.dump(MERMAID_CONFIG, f)
    with open(mmd, "w", encoding="utf-8") as f:
        f.write(src)
    r = subprocess.run(["mmdc", "-q", "-i", mmd, "-o", svg, "-b", "transparent", "-c", cfg],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not os.path.exists(svg):
        raise RuntimeError(f"mermaid 渲染失败（图 {idx}）：{r.stderr[-800:]}")
    with open(svg, encoding="utf-8") as f:
        data = f.read()
    # 让 id 唯一，避免多图样式互相污染
    data = data.replace('id="my-svg"', f'id="mmd-{idx}"').replace("#my-svg", f"#mmd-{idx}")
    # 用 mermaid 给出的自然宽度替换 width=100%，避免整体缩小到不可读
    m = re.search(r'max-width:\s*([0-9.]+)px', data)
    if m:
        w = float(m.group(1))
        data = data.replace('width="100%"', f'width="{int(w)}"', 1)
        data = re.sub(r'max-width:\s*[0-9.]+px;?', '', data, count=1)
    return data


def convert(md_text, tmpdir):
    lines = md_text.splitlines()
    # 剥 frontmatter
    meta = {}
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                for ml in lines[1:j]:
                    if ":" in ml:
                        k, v = ml.split(":", 1)
                        meta[k.strip()] = v.strip()
                lines = lines[j + 1:]
                break
    out, toc, used = [], [], set()
    i, n, dia = 0, len(lines), 0
    title = ""
    while i < n:
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip().lower()
            j = i + 1
            buf = []
            while j < n and not lines[j].startswith("```"):
                buf.append(lines[j]); j += 1
            code = "\n".join(buf)
            if lang == "mermaid":
                dia += 1
                svg = render_mermaid(code, dia, tmpdir)
                out.append(f'<figure class="diagram"><div class="bar"><button type="button" onclick="toggleFit(this)">适应宽度</button></div>{svg}<details><summary>查看图源（Mermaid）</summary><pre><code>{html.escape(code)}</code></pre></details></figure>')
            else:
                out.append(f'<pre><code class="lang-{html.escape(lang)}">{html.escape(code)}</code></pre>')
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl, text = len(m.group(1)), m.group(2).strip()
            if lvl == 1 and not title:
                title = text
                out.append(f"<h1>{inline(text)}</h1>")
            else:
                sid = slugify(re.sub(r"[`*]", "", text), used)
                out.append(f'<h{lvl} id="{sid}">{inline(text)}</h{lvl}>')
                if lvl in (2, 3):
                    toc.append((lvl, sid, re.sub(r"[`*]", "", text)))
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            if len(cells) >= 2 and all(re.match(r"^:?-{2,}:?$", c) for c in cells[1]):
                head, body = cells[0], cells[2:]
            else:
                head, body = None, cells
            t = ["<table>"]
            if head:
                t.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue
        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip()); i += 1
            out.append("<blockquote>" + "<br>".join(inline(b) for b in buf if b) + "</blockquote>")
            continue
        lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if lm:
            # 简单两级列表
            items = []
            while i < n:
                lm2 = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if not lm2:
                    break
                items.append((len(lm2.group(1)), lm2.group(2), lm2.group(3)))
                i += 1
            ordered = items[0][1][0].isdigit()
            tag = "ol" if ordered else "ul"
            h = [f"<{tag}>"]
            open_sub = None
            for ind, mark, text in items:
                if ind > 0:
                    if open_sub is None:
                        open_sub = "ol" if mark[0].isdigit() else "ul"
                        h[-1] = h[-1][:-5] if h[-1].endswith("</li>") else h[-1]
                        h.append(f"<{open_sub}>")
                    h.append(f"<li>{inline(text)}</li>")
                else:
                    if open_sub:
                        h.append(f"</{open_sub}></li>")
                        open_sub = None
                    h.append(f"<li>{inline(text)}</li>")
            if open_sub:
                h.append(f"</{open_sub}></li>")
            h.append(f"</{tag}>")
            out.append("".join(h))
            continue
        if line.strip() == "" or line.strip() == "---":
            i += 1
            continue
        # 段落：吸收连续非空行
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|\||>|\s*([-*]|\d+\.)\s)", lines[i]):
            buf.append(lines[i]); i += 1
        out.append("<p>" + inline(" ".join(b.strip() for b in buf)) + "</p>")
    toc_html = "".join(f'<a class="l{l}" href="#{s}">{html.escape(t)}</a>' for l, s, t in toc)
    meta_html = " · ".join(f"{html.escape(k)}: {html.escape(v)}" for k, v in meta.items() if k in ("type", "audience", "updated", "status"))
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><div class="layout"><nav class="toc"><h2>目录</h2>{toc_html}</nav>
<main><div class="meta">{meta_html}</div>{''.join(out)}</main></div><script>function toggleFit(b){{var f=b.closest('figure');f.classList.toggle('fit');b.textContent=f.classList.contains('fit')?'原始大小':'适应宽度';}}</script></body></html>"""
    return doc


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        md = f.read()
    with tempfile.TemporaryDirectory() as tmp:
        out = convert(md, tmp)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"ok {dst} ({len(out)//1024} KB)")


if __name__ == "__main__":
    main()
