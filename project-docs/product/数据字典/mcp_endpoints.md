## 表：mcp_endpoints

> 业务含义：工作空间对外发布的MCP Server端点：允许Claude Desktop/Cursor等外部MCP客户端通过Streamable HTTP连接并调用受限工具集
> 来源：000102_mcp_endpoints.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 端点ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL；默认 '' | 端点名称 |
| `description` | TEXT | NOT NULL；默认 '' | 端点描述 |
| `enabled` | BOOLEAN | NOT NULL；默认 true | 是否启用 |
| `token_hash` | VARCHAR(64) | NOT NULL；默认 '' | 鉴权令牌哈希（该端点即信任单元，令牌鉴权此端点而非具体某个人） |
| `token_hint` | VARCHAR(16) | NOT NULL；默认 '' | Leading characters of the token for display only |
| `knowledge_base_ids` | JSONB | NOT NULL；默认 '[]' | 限定可访问的知识库ID白名单，为空表示工作空间内全部可访问 |
| `tools` | JSONB | NOT NULL；默认 '[]' | Allowlisted MCP tool names from the endpoint tool catalog |
| `default_agent_id` | VARCHAR(36) | NOT NULL；默认 '' | Agent used by the ask tool when the caller does not name one |
| `rate_limit_per_minute` | INTEGER | NOT NULL；默认 60 | 每分钟调用速率上限 |
| `last_used_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次被调用时间 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_mcp_endpoints_tenant` (`tenant_id`)
- `idx_mcp_endpoints_token_hash` (`token_hash`) [UNIQUE]
- `idx_mcp_endpoints_deleted` (`deleted_at`)

