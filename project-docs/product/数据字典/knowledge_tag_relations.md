## 表：knowledge_tag_relations

> 业务含义：知识条目与标签的多对多关联表
> 来源：000063_knowledge_multi_tags.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `knowledge_id` | VARCHAR(36) | NOT NULL | 知识条目ID |
| `tag_id` | VARCHAR(36) | NOT NULL | 标签ID |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 NOW() | 审计字段：创建时间 |

**索引**：
- `idx_ktr_knowledge` (`knowledge_id`)
- `idx_ktr_tag` (`tag_id`)

