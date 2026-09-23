## 表：im_channels

> 业务含义：IM渠道（企业微信/飞书等）接入配置：每个渠道绑定一个Agent对外提供问答服务
> 来源：000021_im_channel.up.sql, 000023_im_channel_kb_id.up.sql, 000024_im_channel_bot_identity.up.sql, 000028_im_thread_session.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 渠道ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `agent_id` | VARCHAR(36) | NOT NULL | Agent ID this channel is bound to |
| `platform` | VARCHAR(20) | NOT NULL | IM platform: wecom, feishu |
| `name` | VARCHAR(255) | NOT NULL；默认 '' | User-defined channel name for identification |
| `enabled` | BOOLEAN | NOT NULL；默认 true | 是否启用 |
| `mode` | VARCHAR(20) | NOT NULL；默认 'websocket' | Connection mode: webhook or websocket |
| `output_mode` | VARCHAR(20) | NOT NULL；默认 'stream' | Output mode: stream (real-time) or full (wait for complete answer) |
| `credentials` | JSONB | NOT NULL；默认 '{}' | Platform credentials (JSONB): WeCom webhook={corp_id,agent_secret,token,encoding_aes_key,corp_agent_id}, WeCom ws={bot_id,bot_secret}, Feishu={app_id,app_secret,verification_token,encrypt_key} |
| `knowledge_base_id` | VARCHAR(36) | 默认 '' | 该渠道限定的知识库ID |
| `bot_identity` | VARCHAR(255) | NOT NULL；默认 '' | Unique bot identity derived from credentials (e.g. wecom:ws:{bot_id}, feishu:{app_id}). Used to prevent duplicate bot bindings. |
| `session_mode` | VARCHAR(20) | NOT NULL；默认 'user' | Session resolution mode: user (per user+chat, default) or thread (per thread) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_im_channels_tenant` (`tenant_id`)
- `idx_im_channels_agent` (`agent_id`)
- `idx_im_channels_deleted` (`deleted_at`)
- `idx_im_channels_bot_identity` (`bot_identity`) [UNIQUE]

