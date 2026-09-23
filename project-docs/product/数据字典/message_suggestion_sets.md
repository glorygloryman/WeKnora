## 表：message_suggestion_sets

> 业务含义：每条助手消息的追问/推荐问题生成结果的持久化缓存记录（含生成过程用量统计）
> 来源：000067_question_suggestions.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 生成记录ID |
| `tenant_id` | INTEGER | NOT NULL；FK→tenants.id ON DELETE CASCADE | 所属租户ID |
| `session_id` | VARCHAR(36) | NOT NULL | 所属会话ID |
| `assistant_message_id` | VARCHAR(36) | NOT NULL | 对应的助手消息ID |
| `agent_id` | VARCHAR(36) | NOT NULL；默认 '' | 生成时使用的Agent ID |
| `agent_tenant_id` | INTEGER | NOT NULL；默认 0 | 有效/来源租户ID（共享Agent场景） |
| `placement` | VARCHAR(32) | NOT NULL | 展示位置，如 after_answer 回答后展示 |
| `config_hash` | VARCHAR(64) | NOT NULL | 生成配置的哈希，用于同配置下缓存命中判断 |
| `locale` | VARCHAR(16) | NOT NULL；默认 '' | 生成语言/地区 |
| `status` | VARCHAR(16) | NOT NULL | 生成状态：generating生成中/ready已就绪/suppressed已抑制不展示/failed失败 |
| `allow_regenerate` | BOOLEAN | NOT NULL；默认 FALSE | 是否允许用户手动重新生成 |
| `suppression_reason` | VARCHAR(64) | NOT NULL；默认 '' | 被抑制展示的原因 |
| `questions` | JSONB | NOT NULL；默认 '[]'::jsonb | 生成的推荐问题列表 |
| `model_id` | VARCHAR(64) | NOT NULL；默认 '' | 生成所用模型ID |
| `prompt_tokens` | INTEGER | NOT NULL；默认 0 | 输入token数 |
| `completion_tokens` | INTEGER | NOT NULL；默认 0 | 输出token数 |
| `latency_ms` | BIGINT | NOT NULL；默认 0 | 生成耗时(ms) |
| `error_code` | VARCHAR(64) | NOT NULL；默认 '' | 失败时错误码 |
| `lease_until` | TIMESTAMP WITH TIME ZONE | — | 生成任务的并发防重租约到期时间 |
| `generated_at` | TIMESTAMP WITH TIME ZONE | — | 生成完成时间 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_message_suggestion_sets_cache_key` (`tenant_id, assistant_message_id, placement, config_hash, locale`) [UNIQUE]
- `idx_message_suggestion_sets_session` (`tenant_id, session_id, created_at DESC`)
- `idx_message_suggestion_sets_status` (`status, lease_until`)

**外键**：
- `tenant_id` → tenants.id ON DELETE CASCADE

