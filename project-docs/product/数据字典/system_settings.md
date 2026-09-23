## 表：system_settings

> 业务含义：平台级（非工作空间级）运行时可调参数表，供系统管理员在管理界面热更新，无需重启
> 类型：基础设施表，非业务表
> 来源：000053_system_admin_and_settings.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增主键 |
| `key` | VARCHAR(128) | NOT NULL；UNIQUE | 配置项键名，唯一 |
| `value` | JSONB | NOT NULL | 配置值（JSONB，可存int/string/bool/数组） |
| `value_type` | VARCHAR(16) | NOT NULL | 值类型标识：int/string/bool/string_list，决定前端渲染控件与解析方式 |
| `category` | VARCHAR(32) | NOT NULL | 配置分组，如limits/agent/auth，供管理界面分类展示 |
| `description` | TEXT | NOT NULL；默认 '' | 配置项说明 |
| `is_secret` | BOOLEAN | NOT NULL；默认 false | 是否为敏感配置（预留：界面遮罩+确认展示） |
| `requires_restart` | BOOLEAN | NOT NULL；默认 false | 变更后是否需要重启服务才生效（预留提示用） |
| `last_modified_by` | VARCHAR(36) | NOT NULL；默认 '' | 最近一次修改该配置的用户ID |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_system_settings_category` (`category`)

