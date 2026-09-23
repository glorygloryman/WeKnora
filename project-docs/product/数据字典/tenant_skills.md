## 表：tenant_skills

> 业务含义：安装到某个沙箱配置镜像中的技能（Skill）实例：记录安装状态、说明文档、环境变量声明及镜像服务版本
> 来源：000086_tenant_skills.up.sql, 000087_skill_install_transcript.up.sql, 000089_env_vars.up.sql, 000090_skill_catalog.up.sql, 000104_skill_served_version.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 安装记录ID（非镜像内目录名） |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `sandbox_config_id` | VARCHAR(36) | NOT NULL | 安装到的沙箱配置ID |
| `name` | VARCHAR(255) | NOT NULL | Also the directory name inside the image: /opt/weknora/tenant/skills/<name> |
| `version` | VARCHAR(64) | — | 版本号 |
| `description` | TEXT | — | 描述 |
| `instructions` | TEXT | — | SKILL.md正文内容（供Agent二级展开阅读） |
| `bundle_ref` | VARCHAR(1024) | — | 遗留字段：技能压缩包对象引用，新安装留空，改为跟随catalog_id读取目录中心存储的压缩包 |
| `bundle_sha256` | VARCHAR(64) | — | 压缩包内容哈希 |
| `enabled` | BOOLEAN | NOT NULL；默认 TRUE | 是否对Agent可见启用（文件仍留在镜像中，仅控制可见性） |
| `installed_snapshot_id` | VARCHAR(255) | — | 本次安装产生的沙箱快照ID |
| `status` | VARCHAR(32) | NOT NULL | installing安装中/ready就绪/failed失败/removing卸载中 |
| `error` | TEXT | — | 失败错误信息 |
| `installing_since` | TIMESTAMPTZ | — | 开始安装/卸载的时间，用于卡死检测回收 |
| `install_session_id` | VARCHAR(36) | — | 安装该技能时安装器Agent所使用的会话ID（用于查看安装过程） |
| `install_message_id` | VARCHAR(36) | — | Assistant message the installer transcript was streamed into |
| `envs` | JSONB | — | 该技能声明所需的环境变量列表，含可选的工作空间统一值（加密存储） |
| `catalog_id` | VARCHAR(36) | — | 指向tenant_skill_catalog的技能定义ID |
| `served` | JSONB | — | Version still in the image while a newer install is pending or failed: {version,description,instructions,bundle_sha256,bundle_ref,snapshot_id}. NULL when the row itself is what is served. |
| `created_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMPTZ | — | 审计字段：软删除时间 |

**索引**：
- `uq_tenant_skills_config_name` (`sandbox_config_id, name`) [UNIQUE]
- `idx_tenant_skills_catalog` (`catalog_id`)

