## 表：users

> 业务含义：用户账号表：登录凭证、所属默认租户及个人偏好设置
> 来源：000001_agent.up.sql, 000049_user_preferences.up.sql, 000053_system_admin_and_settings.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | Unique identifier of the user |
| `username` | VARCHAR(100) | NOT NULL | Username of the user |
| `email` | VARCHAR(255) | NOT NULL | Email address of the user |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password of the user |
| `avatar` | VARCHAR(500) | — | Avatar URL of the user |
| `tenant_id` | INTEGER | — | Tenant ID that the user belongs to |
| `is_active` | BOOLEAN | NOT NULL；默认 true | Whether the user is active |
| `can_access_all_tenants` | BOOLEAN | NOT NULL；默认 FALSE | 是否可访问所有租户（超级账号能力，独立于系统管理员） |
| `preferences` | JSONB | NOT NULL；默认 '{}'::jsonb | Per-user JSON preferences (memory toggle, future UI knobs) |
| `is_system_admin` | BOOLEAN | NOT NULL；默认 FALSE | Whether the user is a system administrator (independent of tenant roles) |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_users_username` (`username`)
- `idx_users_email` (`email`)
- `idx_users_tenant_id` (`tenant_id`)
- `idx_users_deleted_at` (`deleted_at`)
- `idx_users_is_system_admin` (`is_system_admin`)

**外键**：
- ADD CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL

