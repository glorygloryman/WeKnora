## 表：organizations

> 业务含义：跨租户协作空间（Organization/Space）：多个工作空间之间共享知识库/Agent的组织单元
> 来源：000012_organizations.up.sql, 000046_org_owner_tenant_id.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 组织（空间）ID |
| `name` | VARCHAR(255) | NOT NULL | 组织名称 |
| `description` | TEXT | — | 组织描述 |
| `owner_id` | VARCHAR(36) | NOT NULL | User ID of the organization owner |
| `invite_code` | VARCHAR(32) | — | Unique invitation code for joining the organization |
| `require_approval` | BOOLEAN | 默认 FALSE | Whether joining this organization requires admin approval |
| `invite_code_expires_at` | TIMESTAMP WITH TIME ZONE | — | 当前邀请码的过期时间，为空表示不过期 |
| `invite_code_validity_days` | SMALLINT | NOT NULL；默认 7 | Invite link validity in days: 0=never expire, 1/7/30 days |
| `avatar` | VARCHAR(512) | 默认 '' | 组织头像URL |
| `searchable` | BOOLEAN | NOT NULL；默认 FALSE | When true, space appears in search and can be joined by org ID |
| `member_limit` | INTEGER | NOT NULL；默认 50 | 最大成员（工作空间）数上限，0表示不限制 |
| `owner_tenant_id` | BIGINT | NOT NULL；后续变更：SET NOT NULL | 组织创建时所有者所属的工作空间ID，作为“所有者工作空间”其成员关系不可被删除/变更以防组织失去归属 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_organizations_invite_code` (`invite_code`) [UNIQUE]
- `idx_organizations_owner_id` (`owner_id`)
- `idx_organizations_deleted_at` (`deleted_at`)
- `idx_organizations_owner_tenant` (`owner_tenant_id`)

