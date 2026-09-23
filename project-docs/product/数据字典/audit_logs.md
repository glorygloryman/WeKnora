## 表：audit_logs

> 业务含义：工作空间/平台级操作审计日志：记录RBAC变更、资源增删改、系统管理等关键操作，供安全合规追溯
> 来源：000044_audit_log.up.sql, 000073_kb_activity_scope.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增行ID，兼作分页游标（新→旧排序） |
| `tenant_id` | BIGINT | NOT NULL | 所属工作空间ID，系统级事件为0 |
| `actor_user_id` | VARCHAR(36) | NOT NULL；默认 '' | 操作发起人用户ID |
| `actor_role` | VARCHAR(32) | NOT NULL；默认 '' | 操作发起人当时的角色 |
| `action` | VARCHAR(64) | NOT NULL | 操作类型，如 rbac.member_added、kb.created、system.setting_changed 等点分命名事件 |
| `target_type` | VARCHAR(32) | NOT NULL；默认 '' | 被操作对象类型 |
| `target_id` | VARCHAR(64) | NOT NULL；默认 '' | 被操作对象ID |
| `target_user_id` | VARCHAR(36) | NOT NULL；默认 '' | 当操作对象是用户时的用户ID（如成员变更、密码重置） |
| `request_path` | VARCHAR(512) | NOT NULL；默认 '' | 触发该事件的请求路径 |
| `request_method` | VARCHAR(16) | NOT NULL；默认 '' | 触发该事件的HTTP方法 |
| `outcome` | VARCHAR(16) | NOT NULL；默认 'success' | 结果：success成功/accepted已受理异步执行中/denied被拒绝/failed失败/partial部分成功/canceled已取消 |
| `details` | JSONB | NOT NULL；默认 '{}'::JSONB | 事件详情（JSON，随action不同承载不同字段，如变更前后值），敏感值会被脱敏 |
| `scope_type` | VARCHAR(32) | NOT NULL；默认 '' | 知识库等活动审计场景下的作用域类型，如 knowledge_base |
| `scope_id` | VARCHAR(64) | NOT NULL；默认 '' | 作用域内标识，如 kb id |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 事件发生时间（审计字段，仅追加不可更新/删除） |

**索引**：
- `idx_audit_logs_tenant_id_desc` (`tenant_id, id DESC`)
- `idx_audit_logs_actor` (`actor_user_id`)
- `idx_audit_logs_tenant_action` (`tenant_id, action`)
- `idx_audit_logs_created_at` (`created_at`)
- `idx_audit_logs_tenant_scope_desc` (`tenant_id, scope_type, scope_id, id DESC`)

