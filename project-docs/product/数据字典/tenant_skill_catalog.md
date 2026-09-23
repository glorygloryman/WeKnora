## 表：tenant_skill_catalog

> 业务含义：工作空间技能目录（定义级）：一份技能定义可被安装到多个沙箱配置，压缩包仅在此表持有一份
> 来源：000090_skill_catalog.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 技能定义ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL | 技能名称 |
| `version` | VARCHAR(64) | — | 版本号 |
| `description` | TEXT | — | 描述 |
| `instructions` | TEXT | — | SKILL.md正文 |
| `bundle_ref` | VARCHAR(1024) | — | 技能压缩包对象引用（唯一持有方，卸载安装不会删除该对象） |
| `bundle_sha256` | VARCHAR(64) | — | 压缩包内容哈希 |
| `created_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMPTZ | — | 审计字段：软删除时间 |

**索引**：
- `uq_tenant_skill_catalog_name` (`tenant_id, name`) [UNIQUE]

