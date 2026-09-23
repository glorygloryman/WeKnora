# 项目文档目录

本目录统一沉淀工程文档，遵循 `2026-08-01-v3.4` 文档治理协议（单一事实源见 `/Users/cy/.sentra/document-governance-protocol.md`）。

## 目录约定

- `product/`：L0 长生命单例——总体需求 / 权限矩阵 / 整体实施计划 / api-设计 / 数据字典 / 流程图
- `iterations/`：L2 主题过程——`<主题>/{二次设计.md, 详细实施计划.md, 验收.md}`
- `domain/`：L1 业务领域知识（不依赖技术栈的概念模型、业务规则）
- `decisions/`：L1 设计决策（含外部技术栈版本限制的应对决策）
- `learnings/`：L1 可复用技巧 / 经验 / 实现模式 / 排查思路
- `fix-issue/`：L1 真实故障复盘与规避准则
- `reports/`：L3 时间序列——评审 / 验收 / 分析报告
- `handoff/`：L3 时间序列——交接 / 停留点
- `deploy/`：部署 / 环境 / 发版 / 运维 / 迁移落盘
- `archive/`：废弃方案、早期参考资料与退役归档
- `_meta/`：目录索引与机器可读元数据（`doc-catalog.yaml`、`harness-install.yaml`）

## 落盘规则

- 工程文档文件名默认 `YYYY-MM-DD-中文主题.md`；**豁免**：`product/**` 内部文件、`iterations/<主题>/` 主题目录本身（`iterations/<主题>/*.md` 内部文件仍须带日期前缀）
- 文档路由优先级：用户明确要求 > 仓库映射 > 全局默认约定 > skill / 命令默认路径
- 保存前固定步骤：语义分类 → 仓库映射 → 准入校验 → 命名校验 → 目录合并豁免校验 → `product/` 写入约束（若命中） → 落盘 → 索引维护
- `fix-issue/` 仅接收同时具备「问题现象 / 根因分析 / 修复动作或规避准则 / 真实来源」的文档

## 索引维护

本文件与 `_meta/doc-catalog.yaml` 同时在位，即表示本工程**已启用文档目录索引**。缺任一份，`retire-docs` 会整体拒绝执行，`save-*` 系列的索引维护步骤会静默空转。

- 索引写入只走 `sentra-catalog-upsert.py`，禁止手工整体重写 `doc-catalog.yaml`
- 文档状态取 `draft` / `approved` / `active` / `completed` / `superseded` 五值**封闭全集**；没有「已归档」状态值——归档事实由「文件在不在 `archive/` 下」与「条目还在不在索引里」两个载体表达
- `type=iteration-plan`（文件名含「实施计划 / 实施清单 / 实施方案 / 落地清单 / plan / roadmap / 路线图」）与 `type=iteration-acceptance`（文件名含「验收 / acceptance」）按协议 §12.1 规则 A / A2 **跳过索引**
- 归档动作分两种，文件处理相同、索引处置相反：**G1 彻底归档**（`/archive-stale-iterations`，从索引**删条目**，只用于 `iterations/` 同目录同 base 多版本）与 **G2 退役归档**（`/retire-docs`，索引条目**保留**并翻 `status` / `canonical` / `path`、记 `retire` 原值块）

> **逐文件索引是可选项**：本文件默认只声明目录约定，不逐篇列文档。需要时自行添加一个「文档索引」段，相关技能检测到该段存在后才会同步维护其中的条目。
