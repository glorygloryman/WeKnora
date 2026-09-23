## 表：im_channel_sessions

> 业务含义：IM平台用户/群聊与WeKnora会话的映射表，实现企业微信/飞书等IM渠道消息与内部会话的绑定
> 来源：000021_im_channel.up.sql, 000028_im_thread_session.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 映射记录ID |
| `platform` | VARCHAR(20) | NOT NULL | IM platform identifier: wecom, feishu, etc. |
| `user_id` | VARCHAR(128) | NOT NULL | Platform-specific user identifier |
| `chat_id` | VARCHAR(128) | NOT NULL；默认 '' | Platform-specific chat/group identifier, empty for direct messages |
| `session_id` | VARCHAR(36) | NOT NULL；FK→sessions.id ON DELETE CASCADE | Associated WeKnora session ID |
| `tenant_id` | BIGINT | NOT NULL | Tenant that owns this channel mapping |
| `agent_id` | VARCHAR(36) | 默认 '' | Custom agent ID used for this channel, empty for default |
| `status` | VARCHAR(20) | NOT NULL；默认 'active' | Channel status: active, paused, expired |
| `metadata` | JSONB | 默认 '{}' | Platform-specific extra data (JSON) |
| `im_channel_id` | VARCHAR(36) | 默认 '' | 关联的im_channels渠道ID |
| `thread_id` | VARCHAR(128) | NOT NULL；默认 '' | Platform thread identifier for thread-based sessions. Empty for user-mode sessions. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_channel_lookup` (`platform, user_id, chat_id, tenant_id`) [UNIQUE]
- `idx_im_channel_tenant` (`tenant_id`)
- `idx_im_channel_session` (`session_id`)
- `idx_im_channel_deleted` (`deleted_at`)
- `idx_im_channel_sessions_channel` (`im_channel_id`)
- `idx_channel_thread_lookup` (`platform, chat_id, thread_id, tenant_id`) [UNIQUE]
- `idx_channel_lookup` (`platform, user_id, chat_id, tenant_id, agent_id`) [UNIQUE]
- `idx_channel_thread_lookup` (`platform, chat_id, thread_id, tenant_id, agent_id`) [UNIQUE]

**外键**：
- `session_id` → sessions.id ON DELETE CASCADE

