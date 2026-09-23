## 表：fork_snapshot_leases

> 业务含义：会话Fork（分支）功能中，创建分支会话行之前先落库的沙箱快照租约，防止创建过程崩溃导致快照孤儿无法回收
> 类型：基础设施表，非业务表
> 来源：000098_fork_snapshot_lease.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `snapshot_id` | VARCHAR(128) | PRIMARY KEY | 沙箱快照ID，主键 |
| `tenant_id` | BIGINT | NOT NULL；默认 0 | 所属租户ID |
| `sandbox_config_id` | VARCHAR(36) | NOT NULL；默认 '' | 所属沙箱配置ID |
| `created_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：创建时间 |

**索引**：
- `idx_fork_snapshot_leases_created_at` (`created_at`)

