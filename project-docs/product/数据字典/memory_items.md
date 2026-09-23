## 表：memory_items

> 业务含义：单条长期记忆陈述：从对话中抽取或用户显式要求记住的关于该用户的事实/偏好/画像/任务/兴趣
> 来源：000084_memory.up.sql, 000094_memory_consistency.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记忆条目ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `subject_id` | VARCHAR(512) | NOT NULL | 所属记忆空间的主体标识 |
| `kind` | VARCHAR(32) | NOT NULL | 记忆类型：profile画像/preference偏好/fact事实/task待办任务/interest长期关注点（画像、偏好、兴趣属于“常驻”类型，会一直注入提示词；事实、任务属于“情境”类型，按需检索召回） |
| `content` | TEXT | NOT NULL | 记忆陈述文本 |
| `topic` | VARCHAR(255) | NOT NULL；默认 '' | 该陈述所指向的可读主题名（如“在用的数据库”） |
| `normalized_key` | VARCHAR(255) | NOT NULL；默认 '' | 主题归一化后的键，用于同主题新记忆自动覆盖旧记忆（解决前后矛盾陈述） |
| `importance` | SMALLINT | NOT NULL；默认 3 | 重要性评分（1-5） |
| `origin` | VARCHAR(16) | NOT NULL；默认 'extracted' | 来源：explicit用户显式要求记住/extracted后台自动抽取/manual记忆管理器中手工创建或编辑 |
| `status` | VARCHAR(16) | NOT NULL；默认 'active' | 状态：active生效中/superseded已被新记忆覆盖/archived已归档(容量淘汰)/pending系统推测但待用户确认(从不注入提示词) |
| `source_session_id` | VARCHAR(36) | — | 来源会话ID |
| `source_message_id` | VARCHAR(36) | — | 来源消息ID |
| `valid_from` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 生效起始时间 |
| `invalid_at` | TIMESTAMP WITH TIME ZONE | — | 失效时间 |
| `expires_at` | TIMESTAMP WITH TIME ZONE | — | 该陈述不再值得召回的过期时间（用于时效性任务类记忆） |
| `superseded_by` | VARCHAR(36) | — | 覆盖该记忆的新记忆条目ID |
| `last_used_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次被召回使用时间 |
| `use_count` | INTEGER | NOT NULL；默认 0 | 被召回使用次数 |
| `replaces_id` | VARCHAR(36) | NOT NULL；默认 '' | 本条记忆所替换的旧记忆条目ID（矛盾覆盖场景） |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_memory_items_scope` (`tenant_id, subject_id, status`)
- `idx_memory_items_key` (`tenant_id, subject_id, normalized_key`)
- `idx_memory_replaces` (`tenant_id, subject_id, replaces_id, status`)

