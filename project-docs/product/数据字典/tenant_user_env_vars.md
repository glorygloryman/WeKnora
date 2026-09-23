## 表：tenant_user_env_vars

> 业务含义：按调用主体（用户/IM用户等）维度的个人环境变量表：为沙箱执行/特定技能提供个人化的密钥等变量值
> 来源：000089_env_vars.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 记录ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `principal_type` | VARCHAR(32) | NOT NULL | 调用主体类型 |
| `principal_id` | VARCHAR(512) | NOT NULL | 调用主体标识 |
| `sandbox_config_id` | VARCHAR(36) | NOT NULL | 所属沙箱配置ID |
| `skill_id` | VARCHAR(36) | NOT NULL；默认 '' | 所属技能ID，空表示作用于整个沙箱配置的每次执行 |
| `name` | VARCHAR(255) | NOT NULL | 环境变量名 |
| `value` | TEXT | — | AES-GCM encrypted. Never returned by any endpoint. |
| `created_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：更新时间 |

**索引**：
- `uq_user_env_var` (`tenant_id, principal_type, principal_id, sandbox_config_id, skill_id, name`) [UNIQUE]
- `idx_user_env_var_skill` (`tenant_id, skill_id`)
- `idx_user_env_var_config` (`tenant_id, sandbox_config_id`)

