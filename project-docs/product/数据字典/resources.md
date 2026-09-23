## 表：resources

> 业务含义：文件/对象统一注册表：为每个物理存储对象分配稳定的应用层引用handle，实现跨会话/跨知识库的文件身份与去重
> 来源：000069_resource_registry.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 资源ID |
| `handle` | VARCHAR(22) | NOT NULL；UNIQUE | 对外暴露的稳定引用短句柄（resource://<handle>），API/富文本/LLM提示词中使用它而非物理路径 |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `storage_backend_id` | VARCHAR(36) | — | 存储于的具体存储后端实例ID |
| `provider` | VARCHAR(32) | NOT NULL | 物理存储服务商标识 |
| `physical_path` | TEXT | NOT NULL | 物理存储路径（内部使用，不对外暴露） |
| `location_hash` | VARCHAR(64) | NOT NULL | 物理位置哈希，用于同租户内位置去重 |
| `kind` | VARCHAR(32) | NOT NULL；默认 'file' | 资源种类，默认file |
| `mime_type` | VARCHAR(255) | NOT NULL；默认 '' | MIME类型 |
| `original_name` | VARCHAR(1024) | NOT NULL；默认 '' | 原始文件名 |
| `size` | BIGINT | NOT NULL；默认 0 | 文件大小(字节) |
| `content_hash` | VARCHAR(64) | NOT NULL；默认 '' | 内容哈希（SHA-256），用于内容去重 |
| `lifecycle` | VARCHAR(16) | NOT NULL；默认 'persistent' | 生命周期：persistent永久/temporary临时（会随会话等过期清理） |
| `expires_at` | TIMESTAMP | — | 临时资源的过期时间 |
| `state` | VARCHAR(16) | NOT NULL；默认 'active' | 状态：active有效/deleted已删除 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_resources_tenant_location` (`tenant_id, location_hash`) [UNIQUE]
- `idx_resources_tenant` (`tenant_id`)
- `idx_resources_backend` (`storage_backend_id`)

