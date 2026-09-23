## 表：knowledge_tags

> 业务含义：知识库内的标签（分类）定义，用于给文档/FAQ分块打标签分类
> 来源：000001_agent.up.sql, 000010_add_seq_id.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 标签ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `name` | VARCHAR(128) | NOT NULL | 标签名称，同一知识库内唯一 |
| `color` | VARCHAR(32) | — | 标签展示颜色 |
| `sort_order` | INTEGER | NOT NULL；默认 0 | 同知识库内排序序号 |
| `seq_id` | BIGINT | NOT NULL；默认 nextval('knowledge_tags_seq_id_seq')*/；后续变更：SET DEFAULT nextval('knowledge_tags_seq_id_seq') | 自增序列ID，供外部API引用 |
| `created_at` | TIMESTAMPTZ | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMPTZ | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMPTZ | — | 审计字段：软删除时间 |

**索引**：
- `idx_knowledge_tags_kb_name` (`tenant_id, knowledge_base_id, name`) [UNIQUE]
- `idx_knowledge_tags_kb` (`tenant_id, knowledge_base_id`)
- `idx_knowledge_tags_seq_id` (`seq_id`) [UNIQUE]

