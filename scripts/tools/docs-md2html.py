#!/usr/bin/env python3
"""把本仓 product/domain 的 Markdown 转成自带目录与样式的单文件 HTML。

只覆盖本仓文档实际用到的语法子集：标题 / 表格 / 围栏代码块（mermaid 单独走 div）
/ 引用块 / 有序无序列表 / 水平线 / 段落，行内支持 **粗体**、`代码`、[链接](url)。
不引入外部 Markdown 库——环境只保证 python3 标准库可用。
"""
import html
import re
import sys
from pathlib import Path

INLINE_CODE = re.compile(r'`([^`]+)`')
BOLD = re.compile(r'\*\*([^*]+)\*\*')
LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def inline(text: str) -> str:
    # 先转义，再按占位符还原行内结构：顺序反了会把生成的标签自己转义掉
    out = html.escape(text)
    out = INLINE_CODE.sub(lambda m: '<code>' + m.group(1) + '</code>', out)
    out = BOLD.sub(lambda m: '<strong>' + m.group(1) + '</strong>', out)
    out = LINK.sub(lambda m: '<a href="' + m.group(2) + '">' + m.group(1) + '</a>', out)
    out = out.replace('<br/>', '<br>')
    return out


def slugify(text: str, used: dict) -> str:
    s = re.sub(r'[^\w一-鿿]+', '-', text).strip('-').lower() or 'sec'
    n = used.get(s, 0)
    used[s] = n + 1
    return s if n == 0 else f'{s}-{n}'


def convert(md: str):
    lines = md.split('\n')
    out, toc, used = [], [], {}
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        # 围栏代码块
        m = re.match(r'^```(\w*)\s*$', line)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < n and not re.match(r'^```\s*$', lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            body = '\n'.join(buf)
            if lang == 'mermaid':
                # mermaid 只转义，不做行内替换：图定义里的 * ` [ ] 都是语法
                out.append('<div class="mermaid">' + html.escape(body) + '</div>')
            else:
                out.append('<pre><code>' + html.escape(body) + '</code></pre>')
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            lvl, text = len(m.group(1)), m.group(2).strip()
            sid = slugify(text, used)
            out.append(f'<h{lvl} id="{sid}">{inline(text)}</h{lvl}>')
            if lvl in (2, 3):
                toc.append((lvl, sid, text))
            i += 1
            continue

        # 表格：表头行 + 分隔行
        if line.startswith('|') and i + 1 < n and re.match(r'^\|[\s:|-]+\|\s*$', lines[i + 1]):
            def cells(row):
                return [c.strip() for c in row.strip().strip('|').split('|')]
            head = cells(line)
            i += 2
            body = []
            while i < n and lines[i].startswith('|'):
                body.append(cells(lines[i]))
                i += 1
            t = ['<div class="table-wrap"><table><thead><tr>']
            t += [f'<th>{inline(c)}</th>' for c in head]
            t.append('</tr></thead><tbody>')
            for row in body:
                t.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
            t.append('</tbody></table></div>')
            out.append(''.join(t))
            continue

        # 引用块
        if line.startswith('>'):
            buf = []
            while i < n and lines[i].startswith('>'):
                buf.append(lines[i].lstrip('>').strip())
                i += 1
            out.append('<blockquote>' + '<br>'.join(inline(b) for b in buf if b) + '</blockquote>')
            continue

        # 水平线
        if re.match(r'^-{3,}\s*$', line):
            out.append('<hr>')
            i += 1
            continue

        # 列表（有序 / 无序，只做一层——本仓文档没有更深的嵌套）
        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if m:
            ordered = bool(re.match(r'^\d+\.$', m.group(2)))
            tag = 'ol' if ordered else 'ul'
            items = []
            while i < n:
                mm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', lines[i])
                if not mm:
                    break
                items.append(mm.group(3))
                i += 1
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
            continue

        # 空行
        if not line.strip():
            i += 1
            continue

        # 段落：连续非空、非结构行合成一段
        buf = []
        while i < n and lines[i].strip() and not re.match(
                r'^(#{1,6}\s|```|\||>|-{3,}\s*$|\s*([-*]|\d+\.)\s)', lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append('<p>' + inline(' '.join(buf)) + '</p>')
        else:
            i += 1

    return '\n'.join(out), toc


TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root {
  --bg: #ffffff; --fg: #1f2328; --muted: #656d76; --border: #d1d9e0;
  --accent: #0969da; --code-bg: #f6f8fa; --quote-bg: #fff8e5; --quote-bar: #d4a72c;
  --thead: #f6f8fa; --row: #fbfcfd; --sidebar: #f6f8fa;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117; --fg: #e6edf3; --muted: #9198a1; --border: #3d444d;
    --accent: #4493f8; --code-bg: #151b23; --quote-bg: #2a1e05; --quote-bar: #d4a72c;
    --thead: #151b23; --row: #11161d; --sidebar: #010409;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.75 -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB",
        "Microsoft YaHei", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.layout { display: flex; align-items: flex-start; max-width: 1500px; margin: 0 auto; }
nav.toc {
  position: sticky; top: 0; flex: 0 0 290px; max-height: 100vh; overflow-y: auto;
  padding: 28px 18px; background: var(--sidebar); border-right: 1px solid var(--border);
  font-size: 13.5px;
}
nav.toc h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted); margin: 0 0 12px; border: 0; padding: 0; }
nav.toc a { display: block; padding: 4px 0 4px 0; color: var(--fg);
  text-decoration: none; border-left: 2px solid transparent; padding-left: 10px; }
nav.toc a:hover { color: var(--accent); border-left-color: var(--accent); }
nav.toc a.lvl3 { padding-left: 26px; color: var(--muted); font-size: 12.5px; }
main { flex: 1 1 auto; min-width: 0; padding: 36px 48px 120px; }
h1 { font-size: 30px; margin: 0 0 8px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
h2 { font-size: 23px; margin: 44px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
h3 { font-size: 18.5px; margin: 30px 0 10px; }
h4 { font-size: 16px; margin: 22px 0 8px; }
p { margin: 12px 0; }
a { color: var(--accent); }
code { background: var(--code-bg); border-radius: 5px; padding: .15em .4em;
  font: 13.5px/1.5 ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; }
pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px;
  padding: 14px 16px; overflow-x: auto; }
pre code { background: none; padding: 0; font-size: 13px; }
blockquote { margin: 16px 0; padding: 12px 16px; background: var(--quote-bg);
  border-left: 4px solid var(--quote-bar); border-radius: 0 6px 6px 0; }
hr { border: 0; border-top: 1px solid var(--border); margin: 36px 0; }
ul, ol { padding-left: 26px; }
li { margin: 5px 0; }
.table-wrap { overflow-x: auto; margin: 16px 0; }
table { border-collapse: collapse; width: 100%; font-size: 14.5px; }
th, td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; vertical-align: top; }
th { background: var(--thead); font-weight: 600; white-space: nowrap; }
tbody tr:nth-child(even) { background: var(--row); }
.figure { margin: 22px 0; background: var(--code-bg); border: 1px solid var(--border);
  border-radius: 8px; }
.figure-bar { display: flex; gap: 6px; align-items: center; padding: 8px 10px;
  border-bottom: 1px solid var(--border); font-size: 12.5px; color: var(--muted); }
.figure-bar button { font: inherit; color: var(--fg); background: var(--bg);
  border: 1px solid var(--border); border-radius: 6px; padding: 3px 10px; cursor: pointer; }
.figure-bar button:hover { border-color: var(--accent); color: var(--accent); }
.figure-bar .spacer { flex: 1; }
/* safe center：图比版面窄时居中，比版面宽时退回左对齐——
   普通 center 会把溢出部分从左侧裁掉且滚不回来 */
.mermaid { padding: 18px; overflow: auto; display: flex; justify-content: safe center; }
.mermaid svg { max-width: none !important; }
.mermaid-fallback { color: var(--muted); font-size: 13px; text-align: left; }
@media (max-width: 1000px) {
  nav.toc { display: none; }
  main { padding: 24px 18px 80px; }
}
</style>
</head>
<body>
<div class="layout">
<nav class="toc"><h2>目录</h2>__TOC__</nav>
<main>__BODY__</main>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<script>
(function () {
  var blocks = Array.prototype.slice.call(document.querySelectorAll('.mermaid'));

  // 离线打开时 CDN 取不到渲染库：把图的源码原样留在页面上，正文照常可读
  if (!window.mermaid) {
    blocks.forEach(function (el) {
      var src = el.textContent;
      el.innerHTML = '<p class="mermaid-fallback">（流程图需联网加载渲染库，以下为图的源码）</p><pre><code></code></pre>';
      el.querySelector('code').textContent = src;
    });
    return;
  }

  var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  // useMaxWidth:false 让图按自然尺寸出图。大流程图被压到正文宽度后字号只剩三成，
  // 根本读不清；宁可让容器横向滚动，再配上缩放按钮。
  mermaid.initialize({
    startOnLoad: false, theme: dark ? 'dark' : 'default',
    flowchart: { htmlLabels: true, useMaxWidth: false },
    securityLevel: 'loose'
  });

  mermaid.run({ nodes: blocks }).then(decorate).catch(decorate);

  function decorate() {
    blocks.forEach(function (el) {
      var svg = el.querySelector('svg');
      if (!svg) return;

      var vb = (svg.getAttribute('viewBox') || '').split(/\s+/);
      var natural = parseFloat(vb[2]) || svg.getBoundingClientRect().width;
      if (!natural) return;

      var bar = document.createElement('div');
      bar.className = 'figure-bar';
      bar.innerHTML = '<button data-act="out">− 缩小</button>'
                    + '<button data-act="in">+ 放大</button>'
                    + '<button data-act="fit">适应宽度</button>'
                    + '<button data-act="reset">原始大小</button>'
                    + '<span class="spacer"></span><span class="pct">100%</span>';
      bar.title = '图宽于版面时可在图框内横向拖动';

      var wrap = document.createElement('div');
      wrap.className = 'figure';
      el.parentNode.insertBefore(wrap, el);
      wrap.appendChild(bar);
      wrap.appendChild(el);

      var scale = 1;
      function apply() {
        svg.style.width = (natural * scale) + 'px';
        svg.style.height = 'auto';
        bar.querySelector('.pct').textContent = Math.round(scale * 100) + '%';
      }
      bar.addEventListener('click', function (e) {
        var act = e.target.getAttribute('data-act');
        if (!act) return;
        if (act === 'in') scale = Math.min(scale * 1.25, 4);
        else if (act === 'out') scale = Math.max(scale / 1.25, 0.15);
        else if (act === 'reset') scale = 1;
        else if (act === 'fit') scale = Math.min(1, (el.clientWidth - 36) / natural);
        apply();
      });

      // 首屏在「适应宽度」和「不小于 60%」之间取折中：
      // 宽图硬压到容器宽度后字号只剩两三成，横向滚动比读不清强。
      scale = Math.min(1, Math.max(0.6, (el.clientWidth - 36) / natural));
      apply();
    });
  }
})();
</script>
</body>
</html>
'''


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    md = src.read_text(encoding='utf-8')
    body, toc = convert(md)
    m = re.search(r'^#\s+(.*)$', md, re.M)
    title = m.group(1).strip() if m else src.stem
    toc_html = ''.join(
        f'<a class="lvl{lvl}" href="#{sid}">{html.escape(text)}</a>' for lvl, sid, text in toc)
    out = (TEMPLATE.replace('__TITLE__', html.escape(title))
                   .replace('__TOC__', toc_html)
                   .replace('__BODY__', body))
    dst.write_text(out, encoding='utf-8')
    print(f'{dst}  ({len(out)} 字节, 目录 {len(toc)} 项)')


if __name__ == '__main__':
    main()
