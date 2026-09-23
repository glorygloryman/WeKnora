## 表：message_suggestion_events

> 业务含义：推荐问题的曝光/点击/关闭/重新生成等产品分析埋点事件表，与安全审计日志分离
> 来源：000067_question_suggestions.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增主键 |
| `tenant_id` | INTEGER | NOT NULL；FK→tenants.id ON DELETE CASCADE | 所属租户ID |
| `session_id` | VARCHAR(36) | NOT NULL | 所属会话ID |
| `suggestion_set_id` | VARCHAR(36) | NOT NULL；FK→message_suggestion_sets.id ON DELETE CASCADE | 关联的推荐问题集合ID |
| `question_id` | VARCHAR(64) | NOT NULL；默认 '' | 被操作的具体问题ID |
| `event_type` | VARCHAR(32) | NOT NULL | 事件类型：impression曝光/click点击/dismiss关闭/regenerate重新生成 |
| `actor_id` | VARCHAR(512) | NOT NULL；默认 '' | 触发事件的调用主体标识 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |

**索引**：
- `idx_message_suggestion_events_set` (`suggestion_set_id, created_at`)
- `idx_message_suggestion_events_session` (`tenant_id, session_id, created_at`)
- `idx_message_suggestion_events_type` (`event_type, created_at`)

**外键**：
- `suggestion_set_id` → message_suggestion_sets.id ON DELETE CASCADE
- `tenant_id` → tenants.id ON DELETE CASCADE

