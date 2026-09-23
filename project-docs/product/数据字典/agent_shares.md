## 表：agent_shares

> 业务含义：自定义Agent共享到组织（空间）的记录，实现跨租户Agent访问授权
> 来源：000012_organizations.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 共享记录ID |
| `agent_id` | VARCHAR(36) | NOT NULL | 被共享的Agent ID |
| `organization_id` | VARCHAR(36) | NOT NULL；FK→organizations.id ON DELETE CASCADE | 共享到的组织ID |
| `shared_by_user_id` | VARCHAR(36) | NOT NULL | 发起共享的用户ID |
| `source_tenant_id` | INTEGER | NOT NULL | Original tenant ID of the agent |
| `permission` | VARCHAR(32) | NOT NULL；默认 'viewer' | Access permission: viewer or editor |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_agent_shares_agent_org` (`agent_id, source_tenant_id, organization_id`) [UNIQUE]
- `idx_agent_shares_agent_id` (`agent_id`)
- `idx_agent_shares_org_id` (`organization_id`)
- `idx_agent_shares_source_tenant` (`source_tenant_id`)
- `idx_agent_shares_deleted_at` (`deleted_at`)

**外键**：
- FOREIGN KEY (agent_id, source_tenant_id) REFERENCES custom_agents(id, tenant_id) ON DELETE CASCADE
- `organization_id` → organizations.id ON DELETE CASCADE

