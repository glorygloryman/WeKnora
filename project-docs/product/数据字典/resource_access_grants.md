## 表：resource_access_grants

> 业务含义：资源的临时可撤销访问令牌表，用于生成限时的文件直链访问凭证
> 类型：基础设施表，非业务表
> 来源：000069_resource_registry.up.sql, 000072_auth_timestamp_tz.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 授权记录ID |
| `token_hash` | VARCHAR(64) | NOT NULL；UNIQUE | 访问令牌哈希，用于鉴权查找 |
| `resource_id` | VARCHAR(36) | NOT NULL；FK→resources.id ON DELETE CASCADE | 被授权访问的资源ID |
| `access_scope` | VARCHAR(16) | NOT NULL；默认 'read' | 访问范围，默认read只读 |
| `expires_at` | TIMESTAMP | NOT NULL；后续变更：TYPE TIMESTAMP WITH TIME ZONE USING expires_at AT TIME ZONE 'UTC' | 过期时间 |
| `revoked_at` | TIMESTAMP | 后续变更：TYPE TIMESTAMP WITH TIME ZONE USING revoked_at AT TIME ZONE 'UTC' | 吊销时间 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP；后续变更：TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC' | 审计字段：创建时间 |

**索引**：
- `idx_resource_access_grants_resource` (`resource_id`)
- `idx_resource_access_grants_expires` (`expires_at`)

**外键**：
- `resource_id` → resources.id ON DELETE CASCADE

