## 表：kb_shares

> 业务含义：知识库共享到组织（空间）的记录，实现跨租户知识库访问授权
> 来源：000012_organizations.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 共享记录ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL；FK→knowledge_bases.id ON DELETE CASCADE | 被共享的知识库ID |
| `organization_id` | VARCHAR(36) | NOT NULL；FK→organizations.id ON DELETE CASCADE | 共享到的组织ID |
| `shared_by_user_id` | VARCHAR(36) | NOT NULL | 发起共享的用户ID |
| `source_tenant_id` | INTEGER | NOT NULL | Original tenant ID of the knowledge base for cross-tenant embedding model access |
| `permission` | VARCHAR(32) | NOT NULL；默认 'viewer' | Access permission level: admin, editor, or viewer |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_kb_shares_kb_org` (`knowledge_base_id, organization_id`) [UNIQUE]
- `idx_kb_shares_kb_id` (`knowledge_base_id`)
- `idx_kb_shares_org_id` (`organization_id`)
- `idx_kb_shares_source_tenant` (`source_tenant_id`)
- `idx_kb_shares_deleted_at` (`deleted_at`)

**外键**：
- `knowledge_base_id` → knowledge_bases.id ON DELETE CASCADE
- `organization_id` → organizations.id ON DELETE CASCADE

