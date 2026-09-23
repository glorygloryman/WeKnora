## 表：mcp_services

> 业务含义：租户配置的MCP（Model Context Protocol）外部工具服务连接定义
> 来源：000001_agent.up.sql, 000017_mcp_builtin.up.sql, 000092_mcp_metadata.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | MCP服务ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL | 服务名称 |
| `description` | TEXT | — | 服务描述 |
| `enabled` | BOOLEAN | 默认 true | 是否启用 |
| `transport_type` | VARCHAR(50) | NOT NULL | 传输方式：sse/http-streamable/stdio |
| `url` | VARCHAR(512) | — | 服务地址（SSE/HTTP方式必填） |
| `headers` | JSONB | — | 自定义HTTP请求头 |
| `auth_config` | JSONB | — | 认证配置：类型(api_key/bearer/oauth)及对应密钥/令牌（加密存储） |
| `advanced_config` | JSONB | — | 高级配置：超时时间、重试次数、重试间隔 |
| `stdio_config` | JSONB | — | stdio传输方式的启动命令与参数（如 uvx/npx） |
| `env_vars` | JSONB | — | stdio传输方式下注入的环境变量 |
| `is_builtin` | BOOLEAN | NOT NULL；默认 false | 是否为内置MCP服务（对所有工作空间可见） |
| `usage_instructions` | TEXT | NOT NULL；默认 '' | 面向Agent的使用说明文本，独立维护不被目录刷新覆盖 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_mcp_services_tenant_id` (`tenant_id`)
- `idx_mcp_services_enabled` (`enabled`)
- `idx_mcp_services_deleted_at` (`deleted_at`)
- `idx_mcp_services_is_builtin` (`is_builtin`)

