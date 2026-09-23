## 表：mcp_tool_approvals

> 业务含义：MCP服务下各工具的启用/人工审批策略覆盖表，实现高风险工具调用前的人工确认
> 来源：000042_mcp_tool_approval.up.sql, 000091_mcp_tool_enabled.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 记录ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `service_id` | VARCHAR(36) | NOT NULL；FK→mcp_services.id ON DELETE CASCADE | 所属MCP服务ID |
| `tool_name` | VARCHAR(512) | NOT NULL | 工具名称 |
| `require_approval` | BOOLEAN | NOT NULL；默认 false | 调用该工具前是否需要用户在界面中人工审批 |
| `enabled` | BOOLEAN | NOT NULL；默认 true | 该工具是否对Agent可见/启用 |
| `created_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_mcp_tool_approvals_tenant_svc_tool` (`tenant_id, service_id, tool_name`) [UNIQUE]
- `idx_mcp_tool_approvals_service_id` (`service_id`)

**外键**：
- `service_id` → mcp_services.id ON DELETE CASCADE

