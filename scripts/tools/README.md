# scripts/tools — 开发辅助脚本

## docs-md2html.py

把 `project-docs/` 下的 Markdown 转成自带目录、样式与流程图渲染的单文件 HTML，
供不便在编辑器里读 Markdown 的人直接用浏览器打开。

```bash
python3 scripts/tools/docs-md2html.py <输入.md> <输出.html>
```

例（改完 Markdown 后重新生成 HTML）：

```bash
python3 scripts/tools/docs-md2html.py \
  "project-docs/product/知识库入库与检索流程.md" \
  "project-docs/product/知识库入库与检索流程.html"
```

说明：

- 只覆盖本仓文档实际用到的 Markdown 子集（标题 / 表格 / 围栏代码块 / 引用块 /
  单层列表 / 水平线 / 段落，行内支持粗体、行内代码、链接），不引入第三方
  Markdown 库——环境只保证 `python3` 标准库可用。
- ` ```mermaid ` 代码块渲染成流程图，并带「缩小 / 放大 / 适应宽度 / 原始大小」按钮。
  渲染库走 CDN；离线打开时自动退回展示图的源码，正文不受影响。
- 首屏缩放取「适应宽度」与 60% 的较大者：宽图硬压到版面宽度后字号只剩两三成，
  横向滚动比读不清强。
