## 表：tenant_invitations

> 业务含义：工作空间邀请表：管理员发起的定向邀请或邀请链接，用户接受后生成tenant_members记录
> 来源：000048_tenant_invitations.up.sql, 000054_invitation_tokens.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 邀请ID |
| `tenant_id` | INTEGER | NOT NULL | 邀请所属工作空间ID |
| `invitee_user_id` | VARCHAR(36) | NOT NULL；默认 ''*/；后续变更：SET DEFAULT '' | 被邀请用户ID，邀请链接类行为空串（无特定被邀请人） |
| `invited_by` | VARCHAR(36) | — | 发起邀请的用户ID |
| `role` | VARCHAR(20) | NOT NULL | 接受邀请后将获得的角色 |
| `status` | VARCHAR(20) | NOT NULL；默认 'pending' | 邀请状态：pending待处理/accepted已接受/declined已拒绝/revoked已撤回/expired已过期 |
| `message` | VARCHAR(500) | — | 邀请附言 |
| `expires_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | 邀请过期时间 |
| `responded_at` | TIMESTAMP WITH TIME ZONE | — | 被处理（接受/拒绝/撤回/过期）的时间 |
| `token` | VARCHAR(64) | NOT NULL；默认 '' | 邀请链接使用的明文注册令牌，定向邀请为空 |
| `accepted_count` | INTEGER | NOT NULL；默认 0 | 该邀请（链接）已被多少人接受注册使用，定向邀请上限为1 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_tenant_invitations_unique_pending` (`tenant_id, invitee_user_id`) [UNIQUE]
- `idx_tenant_invitations_tenant` (`tenant_id`)
- `idx_tenant_invitations_invitee` (`invitee_user_id`)
- `idx_tenant_invitations_unique_pending` (`tenant_id, invitee_user_id`) [UNIQUE]
- `idx_tenant_invitations_token` (`token`) [UNIQUE]

