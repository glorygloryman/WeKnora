## 表：memory_topic_stats

> 业务含义：记忆主题命中次数统计表：某用户反复被问到/提到的主题达到阈值后才升级为“长期关注点(interest)”记忆
> 来源：000084_memory.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记录ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `subject_id` | VARCHAR(512) | NOT NULL | 所属记忆空间的主体标识 |
| `normalized_key` | VARCHAR(255) | NOT NULL | 主题归一化键 |
| `topic` | VARCHAR(255) | NOT NULL；默认 '' | 主题展示名 |
| `hits` | INTEGER | NOT NULL；默认 0 | 该主题被命中（提及/提问）的次数 |
| `last_seen_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次命中时间 |
| `promoted_at` | TIMESTAMP WITH TIME ZONE | — | 升级为interest记忆的时间，为空表示尚未达到阈值 |
| `aliases` | JSONB | NOT NULL；默认 '[]' | 该主题曾经出现过的其他措辞（同义表达），用于精确匹配加速与审计追踪 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_mem_topic_scope` (`tenant_id, subject_id, normalized_key`) [UNIQUE]

