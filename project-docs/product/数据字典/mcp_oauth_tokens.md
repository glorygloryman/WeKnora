## 表：mcp_oauth_tokens

> 业务含义：MCP服务按调用主体（用户/IM用户/嵌入访客等）维度存储的OAuth访问/刷新令牌
> 来源：000062_mcp_oauth.up.sql, 000064_principal_model.up.sql, 000074_mcp_oauth_refresh_lease.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 记录ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `user_id` | VARCHAR(64) | NOT NULL；后续变更：TYPE VARCHAR(512) | 旧版调用主体标识字段，已被principal_type/principal_id取代但保留兼容 |
| `service_id` | VARCHAR(36) | NOT NULL；FK→mcp_services.id ON DELETE CASCADE | 所属MCP服务ID |
| `access_token` | TEXT | — | 访问令牌（加密存储） |
| `refresh_token` | TEXT | — | 刷新令牌（加密存储） |
| `token_type` | VARCHAR(32) | — | 令牌类型 |
| `expires_at` | TIMESTAMP | — | 访问令牌过期时间 |
| `principal_type` | VARCHAR(32) | NOT NULL；后续变更：SET NOT NULL | 调用主体类型：web_user/api_tenant/api_platform/api_external_user/im_user/embed_channel/embed_session/embed_visitor/mcp_endpoint |
| `principal_id` | VARCHAR(512) | NOT NULL；后续变更：SET NOT NULL | 调用主体标识 |
| `refresh_lease_id` | VARCHAR(36) | — | 刷新令牌轮换的分布式租约ID，避免多实例并发刷新冲突 |
| `refresh_lease_until` | TIMESTAMP WITH TIME ZONE | — | 刷新租约到期时间 |
| `created_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_mcp_oauth_tokens_tenant_user_svc` (`tenant_id, user_id, service_id`) [UNIQUE]
- `idx_mcp_oauth_tokens_service_id` (`service_id`)
- `idx_mcp_oauth_tokens_user_id` (`user_id`)
- `idx_mcp_oauth_tokens_tenant_principal_svc` (`tenant_id, principal_type, principal_id, service_id`) [UNIQUE]
- `idx_mcp_oauth_tokens_principal` (`principal_type, principal_id`)

**外键**：
- `service_id` → mcp_services.id ON DELETE CASCADE

