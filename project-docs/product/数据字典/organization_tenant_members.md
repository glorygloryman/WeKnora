## 表：organization_tenant_members

> 业务含义：组织（空间）成员表（按工作空间维度，取代旧的organization_members按用户维度设计），是当前生效的组织成员权限来源
> 来源：000045_org_tenant_members.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记录ID |
| `organization_id` | VARCHAR(36) | NOT NULL；FK→organizations.id ON DELETE CASCADE | 所属组织ID |
| `tenant_id` | INTEGER | NOT NULL | 加入该组织的工作空间ID |
| `role` | VARCHAR(32) | NOT NULL；默认 'viewer' | Tenant role inside the org: admin \| editor \| viewer. |
| `representative_user_id` | VARCHAR(36) | NOT NULL；默认 '' | Display-only: the user who first brought this tenant into the org. |
| `joined_at` | TIMESTAMP WITH TIME ZONE | — | 加入时间 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_org_tenant_members_unique` (`organization_id, tenant_id`) [UNIQUE]
- `idx_org_tenant_members_by_tenant` (`tenant_id`)
- `idx_org_tenant_members_role` (`organization_id, role`)

**外键**：
- `organization_id` → organizations.id ON DELETE CASCADE

