## 表：tenant_disabled_shared_agents

> 业务含义：记录某工作空间主动“隐藏”某个共享进来的Agent（不在自己对话下拉框显示的个人化设置）
> 来源：000012_organizations.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `tenant_id` | BIGINT | NOT NULL | 隐藏该共享Agent的工作空间ID |
| `agent_id` | VARCHAR(36) | NOT NULL | 被隐藏的Agent ID |
| `source_tenant_id` | BIGINT | NOT NULL | 该Agent的来源（所有者）工作空间ID |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |

**索引**：
- `idx_tenant_disabled_shared_agents_tenant_id` (`tenant_id`)

