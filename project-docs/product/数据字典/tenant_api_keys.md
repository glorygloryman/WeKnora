## 表：tenant_api_keys

> 业务含义：工作空间/平台级API Key表：面向程序化集成的可撤销机器凭证，支持按能力(capability)与知识库范围限权
> 来源：000065_tenant_api_keys.up.sql, 000071_platform_api_keys.up.sql, 000072_auth_timestamp_tz.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增主键 |
| `tenant_id` | INTEGER | NOT NULL；FK→tenants.id ON DELETE CASCADE；后续变更：DROP NOT NULL | 所属工作空间ID，平台级Key为NULL |
| `name` | VARCHAR(128) | NOT NULL | Key名称 |
| `key_hash` | VARCHAR(64) | NOT NULL；UNIQUE | Key的哈希值，用于鉴权查找 |
| `api_key` | TEXT | NOT NULL；默认 '' | Key明文（加密存储，展示时解密回传一次） |
| `full_access` | BOOLEAN | NOT NULL；默认 FALSE | 是否为不受能力限制的完全访问Key |
| `knowledge_base_ids` | JSONB | NOT NULL；默认 '[]'::jsonb | 限定可访问的知识库ID白名单，为空表示不限制 |
| `capabilities` | JSONB | NOT NULL；默认 '[]'::jsonb | 受限Key被授予的能力集合：retrieve检索/chat对话/read_agents查看Agent/ingest写入知识/manage_knowledge_bases管理知识库/manage_agents管理Agent/message_history历史消息/manage_models模型管理/manage_mcp_services等约20种细分能力 |
| `last_used_at` | TIMESTAMP | 后续变更：TYPE TIMESTAMP WITH TIME ZONE USING last_used_at AT TIME ZONE 'UTC' | 最近一次使用时间 |
| `expires_at` | TIMESTAMP | 后续变更：TYPE TIMESTAMP WITH TIME ZONE USING expires_at AT TIME ZONE 'UTC' | 过期时间 |
| `revoked_at` | TIMESTAMP | 后续变更：TYPE TIMESTAMP WITH TIME ZONE USING revoked_at AT TIME ZONE 'UTC' | 吊销时间 |
| `scope_type` | VARCHAR(16) | NOT NULL；默认 'tenant' | Key作用域：tenant工作空间级/platform平台级（跨租户管理） |
| `created_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP；后续变更：TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC' | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP；后续变更：TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC' | 审计字段：更新时间 |

**索引**：
- `idx_tenant_api_keys_tenant` (`tenant_id`)
- `idx_tenant_api_keys_revoked_at` (`revoked_at`)
- `idx_tenant_api_keys_scope_type` (`scope_type`)

**外键**：
- `tenant_id` → tenants.id ON DELETE CASCADE

