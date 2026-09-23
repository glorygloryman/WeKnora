## 表：organization_members

> 业务含义：【历史/已废弃】按用户维度的组织成员表，已被按工作空间维度的 organization_tenant_members 取代，代码中不再读写，仅为历史迁移数据保留
> 来源：000012_organizations.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记录ID |
| `organization_id` | VARCHAR(36) | NOT NULL；FK→organizations.id ON DELETE CASCADE | 所属组织ID |
| `user_id` | VARCHAR(36) | NOT NULL | 成员用户ID |
| `tenant_id` | INTEGER | NOT NULL | The tenant ID that the member belongs to |
| `role` | VARCHAR(32) | NOT NULL；默认 'viewer' | Member role: admin, editor, or viewer |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_org_members_org_user` (`organization_id, user_id`) [UNIQUE]
- `idx_org_members_user_id` (`user_id`)
- `idx_org_members_tenant_id` (`tenant_id`)
- `idx_org_members_role` (`role`)

**外键**：
- `organization_id` → organizations.id ON DELETE CASCADE

