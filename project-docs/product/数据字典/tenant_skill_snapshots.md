## 表：tenant_skill_snapshots

> 业务含义：沙箱镜像链路的快照台账：记录每次安装/卸载/重建产生的Provider侧快照及其父子链，防止快照资源泄漏或失联
> 类型：基础设施表，非业务表
> 来源：000086_tenant_skills.up.sql, 000088_skill_snapshot_planned_name.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 安装ID（同时作为快照命名种子） |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `sandbox_config_id` | VARCHAR(36) | NOT NULL | 所属沙箱配置ID |
| `skill_id` | VARCHAR(36) | — | 关联的技能安装记录ID |
| `snapshot_id` | VARCHAR(255) | — | Provider侧返回的快照ID |
| `parent_snapshot_id` | VARCHAR(255) | — | 父快照ID，构成镜像演进链 |
| `generation` | INTEGER | NOT NULL；默认 0 | 快照代数 |
| `trigger` | VARCHAR(16) | NOT NULL | 触发来源：install安装/remove卸载/rebuild重建 |
| `state` | VARCHAR(16) | NOT NULL | building构建中/active当前生效/superseded已被取代/deleted已删除（仅在Provider侧真正删除后写入） |
| `superseded_at` | TIMESTAMPTZ | — | 被取代时间 |
| `planned_name` | VARCHAR(255) | — | Name passed to CreateSnapshot, written before the provider call so an abandoned build stays identifiable |
| `created_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：更新时间 |

**索引**：
- `idx_tenant_skill_snapshots_config` (`sandbox_config_id`)
- `idx_tenant_skill_snapshots_state` (`state`)

