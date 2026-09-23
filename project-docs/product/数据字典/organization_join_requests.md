## 表：organization_join_requests

> 业务含义：组织加入/角色升级申请表，支撑需管理员审批的加入流程
> 来源：000012_organizations.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 申请ID |
| `organization_id` | VARCHAR(36) | NOT NULL；FK→organizations.id ON DELETE CASCADE | 目标组织ID |
| `user_id` | VARCHAR(36) | NOT NULL | 申请人用户ID |
| `tenant_id` | INTEGER | NOT NULL | 申请人所属工作空间ID |
| `status` | VARCHAR(32) | NOT NULL；默认 'pending' | Request status: pending, approved, rejected |
| `requested_role` | VARCHAR(32) | NOT NULL；默认 'viewer' | Role requested by the applicant: admin, editor, viewer |
| `request_type` | VARCHAR(32) | NOT NULL；默认 'join' | join for new member, upgrade for role upgrade |
| `prev_role` | VARCHAR(32) | — | 升级申请场景下的原角色 |
| `message` | TEXT | — | Optional message from the requester |
| `reviewed_by` | VARCHAR(36) | — | User ID of the admin who reviewed the request |
| `reviewed_at` | TIMESTAMP WITH TIME ZONE | — | 审批处理时间 |
| `review_message` | TEXT | — | Optional message from the reviewer |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_org_join_requests_org_user_pending` (`organization_id, user_id`) [UNIQUE]
- `idx_org_join_requests_org_id` (`organization_id`)
- `idx_org_join_requests_user_id` (`user_id`)
- `idx_org_join_requests_status` (`status`)
- `idx_org_join_requests_type` (`request_type`)
- `uq_org_join_requests_pending_per_tenant` (`organization_id, tenant_id, request_type`) [UNIQUE]

**外键**：
- `organization_id` → organizations.id ON DELETE CASCADE

