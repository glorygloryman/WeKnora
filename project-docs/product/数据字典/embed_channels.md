## 表：embed_channels

> 业务含义：网站嵌入式对话组件（Widget）发布配置：把某个Agent以可嵌入外部网站的聊天窗口形式对外发布
> 来源：000060_embed_channels.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 嵌入渠道ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `agent_id` | VARCHAR(36) | NOT NULL；默认 'builtin-quick-answer' | 对外提供服务的Agent ID，默认builtin-quick-answer |
| `name` | VARCHAR(255) | NOT NULL；默认 '' | 渠道名称 |
| `enabled` | BOOLEAN | NOT NULL；默认 true | 是否启用 |
| `publish_token` | VARCHAR(64) | NOT NULL；默认 '' | 对外发布使用的公开令牌（嵌入脚本中携带） |
| `allowed_origins` | JSONB | NOT NULL；默认 '[]' | 允许跨域调用的来源白名单 |
| `welcome_message` | TEXT | NOT NULL；默认 '' | 对话窗口欢迎语 |
| `rate_limit_per_minute` | INTEGER | NOT NULL；默认 30 | Per-IP per-minute request cap for the public embed endpoints |
| `rate_limit_per_day` | INTEGER | NOT NULL；默认 10000 | 该渠道每日请求总量上限（跨所有访客IP），防止公开令牌被滥用 |
| `primary_color` | VARCHAR(32) | NOT NULL；默认 '' | CSS color for embed widget accent (e.g. #0052d9) |
| `page_title` | VARCHAR(255) | NOT NULL；默认 '' | Browser tab title for the embed page |
| `header_title_mode` | VARCHAR(32) | NOT NULL；默认 'channel' | Embed header title source: channel (fixed page title) or session (auto-generated after first message) |
| `show_suggested_questions` | BOOLEAN | NOT NULL；默认 true | When true, embed chat shows suggested starter questions before the first visitor message |
| `widget_position` | VARCHAR(32) | NOT NULL；默认 'bottom-right' | Floating widget corner: bottom-right, bottom-left, top-right, top-left |
| `allow_web_search` | BOOLEAN | NOT NULL；默认 false | 该嵌入组件是否允许触发联网搜索 |
| `allow_memory` | BOOLEAN | NOT NULL；默认 false | 该嵌入组件是否允许使用长期记忆 |
| `allow_file_upload` | BOOLEAN | NOT NULL；默认 false | 该嵌入组件是否允许访客上传文件 |
| `default_locale` | VARCHAR(16) | NOT NULL；默认 '' | 默认界面语言 |
| `webhook_url` | VARCHAR(512) | NOT NULL；默认 '' | HTTPS endpoint for outbound message_sent / message_received events |
| `webhook_secret` | VARCHAR(128) | NOT NULL；默认 '' | Optional HMAC-SHA256 secret for X-WeKnora-Signature header |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_embed_channels_tenant` (`tenant_id`)
- `idx_embed_channels_agent` (`agent_id`)
- `idx_embed_channels_publish_token` (`publish_token`) [UNIQUE]
- `idx_embed_channels_deleted` (`deleted_at`)

