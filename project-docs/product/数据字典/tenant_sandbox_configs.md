## 表：tenant_sandbox_configs

> 业务含义：工作空间的技能沙箱后端配置：定义Agent执行脚本所用的Docker/E2B/Cube等沙箱环境连接信息
> 来源：000082_tenant_sandbox_config.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 沙箱配置ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL | 配置名称 |
| `description` | TEXT | — | 配置描述 |
| `sandbox_type` | VARCHAR(32) | NOT NULL | 沙箱后端类型（如docker/e2b/cube） |
| `config` | JSONB | NOT NULL | 沙箱连接凭证与参数（加密存储） |
| `cordoned_at` | TIMESTAMPTZ | — | 身份信息变更期间的临时封禁标记时间（防止并发操作期间状态不一致），是租约而非永久锁 |
| `created_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMPTZ | — | 审计字段：软删除时间 |

**索引**：
- `idx_tenant_sandbox_configs_tenant` (`tenant_id`)
- `uq_tenant_sandbox_configs_tenant_name` (`tenant_id, name`) [UNIQUE]

