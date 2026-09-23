# learnings/ — 可复用技巧 / 经验 / 实现模式

存放"下次可照用"的可复用技巧、经验、实现模式、排查思路（**无取舍、无故障、无部署语义**）。

## 与邻近目录的区分（存盘决策树，命中即止）

```
1 真炸过？(现象+根因+规避+真实来源)        → fix-issue/
2 "为什么选 X 不选 Y"的取舍？             → decisions/
3 "可复用技巧/模式/方法/排查思路"？        → learnings/（本目录）
4 "部署/环境/发版/运维/迁移落盘"操作？      → deploy/
5 业务概念/规则（不依赖技术栈）？         → domain/
```

## 命名规则
`YYYY-MM-DD-主题.md`

## 文档模板

```
---
tags: [关键词1, 关键词2]
scope: [相关文件/模块路径]
updated: YYYY-MM-DD
type: operational | pattern               # 档位：operational=环境/命令/工作流怪癖；pattern=可复用实现模式/排查思路
confidence: 1-10                          # 信度衰减钩子：observed 8-9 / inferred 4-5 / user-stated 10
source: observed | user-stated | inferred # 信度衰减钩子：来源
---

# Learning：[主题]

## 适用场景
[什么情况下下次可以照用这个技巧/模式]

## 做法
[可复用的实现方案 / 技巧 / 排查思路]

## 为什么有效 / 注意
[原理或边界，避免误用]
```

> `type/confidence/source` 三字段由 `/save-learning` 技能写入（衰减钩子，供召回端按 source/confidence 排序与衰减）。
> 档位差异：`operational` 允许只「适用场景 + 做法」两段（「为什么有效」可省）；`pattern` 三段齐全。
