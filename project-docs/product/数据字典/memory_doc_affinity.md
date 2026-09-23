## 表：memory_doc_affinity

> 业务含义：记录某用户的回答反复引用某份文档的次数，是唯一无需用户主动提供的“个人检索偏好”信号，用于个性化召回排序
> 来源：000084_memory.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记录ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `subject_id` | VARCHAR(512) | NOT NULL | 所属记忆空间的主体标识 |
| `knowledge_id` | VARCHAR(36) | NOT NULL | 被引用的知识条目ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL；默认 '' | 所属知识库ID |
| `title` | VARCHAR(512) | NOT NULL；默认 '' | 文档标题（冗余存储便于展示） |
| `hits` | INTEGER | NOT NULL；默认 0 | 被该用户的回答引用次数 |
| `last_used_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次被引用时间 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_mem_affinity_scope` (`tenant_id, subject_id, knowledge_id`) [UNIQUE]

