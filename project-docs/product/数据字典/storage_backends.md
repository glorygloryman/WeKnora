## 表：storage_backends

> 业务含义：工作空间可配置的对象/文件存储后端实例注册表，支持一个工作空间挂载多个存储实例并按知识库绑定
> 来源：000068_storage_backends.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 存储后端实例ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL | 实例名称 |
| `provider` | VARCHAR(32) | NOT NULL | 存储服务商：local/minio/cos/tos/s3/oss/ks3/obs |
| `config` | JSONB | NOT NULL；默认 '{}' | 连接配置（Endpoint、AccessKey/SecretKey均加密存储、Bucket、路径前缀等，因服务商而异） |
| `source` | VARCHAR(16) | NOT NULL；默认 'user' | 配置来源：user用户在界面创建/env由环境变量派生的只读实例 |
| `status` | VARCHAR(16) | NOT NULL；默认 'active' | 实例状态：active启用/disabled停用 |
| `legacy_alias` | BOOLEAN | NOT NULL；默认 FALSE | 是否为迁移前旧版单一存储配置派生出的兼容别名实例 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_storage_backends_name_tenant` (`tenant_id, name`) [UNIQUE]
- `idx_storage_backends_legacy_alias` (`tenant_id, provider`) [UNIQUE]
- `idx_storage_backends_tenant` (`tenant_id`)

