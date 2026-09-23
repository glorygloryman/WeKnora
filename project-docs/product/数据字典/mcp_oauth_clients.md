## 表：mcp_oauth_clients

> 业务含义：MCP服务的OAuth动态注册客户端凭证缓存，每个(租户,服务)注册一次并复用，避免重复注册
> 来源：000062_mcp_oauth.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 记录ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `service_id` | VARCHAR(36) | NOT NULL；FK→mcp_services.id ON DELETE CASCADE | 所属MCP服务ID |
| `client_id` | VARCHAR(512) | NOT NULL | OAuth客户端ID |
| `client_secret` | TEXT | — | OAuth客户端密钥（加密存储） |
| `redirect_uri` | VARCHAR(1024) | — | OAuth回调地址 |
| `created_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_mcp_oauth_clients_tenant_svc` (`tenant_id, service_id`) [UNIQUE]
- `idx_mcp_oauth_clients_service_id` (`service_id`)

**外键**：
- `service_id` → mcp_services.id ON DELETE CASCADE

