## 表：user_resource_favorites

> 业务含义：用户对知识库/Agent等资源的个人收藏（星标）记录
> 来源：000047_user_resource_favorites.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `user_id` | VARCHAR(36) | NOT NULL | 收藏用户ID |
| `tenant_id` | BIGINT | NOT NULL | 所属工作空间ID |
| `resource_type` | VARCHAR(16) | NOT NULL | 'kb' \| 'agent' (extensible) |
| `resource_id` | VARCHAR(64) | NOT NULL | 被收藏资源ID |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |

**索引**：
- `idx_user_resource_favorites_user_tenant_type_created_at` (`user_id, tenant_id, resource_type, created_at DESC`)
- `idx_user_resource_favorites_tenant_id` (`tenant_id`)

