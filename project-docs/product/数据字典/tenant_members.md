## 表：tenant_members

> 业务含义：工作空间成员表：用户在某工作空间内的角色（RBAC四级角色矩阵）及成员状态
> 来源：000043_tenant_rbac.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 记录ID |
| `user_id` | VARCHAR(36) | NOT NULL | 成员用户ID |
| `tenant_id` | INTEGER | NOT NULL | 所属工作空间ID |
| `role` | VARCHAR(20) | NOT NULL；默认 'contributor' | 工作空间内角色：owner所有者(可删除空间/转让所有权)/admin管理员/contributor贡献者(可创建及编辑自己创建的资源)/viewer仅查看(可运行被标记为viewer可运行的Agent) |
| `status` | VARCHAR(20) | NOT NULL；默认 'active' | 成员状态：active正常/invited已邀请待接受/suspended已被暂停（保留记录但不可登录该空间） |
| `invited_by` | VARCHAR(36) | — | 邀请该成员的管理员用户ID，自助注册为空 |
| `joined_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 成为正式成员的时间 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_tenant_members_user_tenant_unique` (`user_id, tenant_id`) [UNIQUE]
- `idx_tenant_members_tenant_role` (`tenant_id, role`)
- `idx_tenant_members_user` (`user_id`)

