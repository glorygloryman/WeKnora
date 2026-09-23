## 表：user_kb_pins

> 业务含义：用户维度的知识库置顶记录，替代旧的知识库全局置顶字段，实现按用户个性化的知识库排序
> 来源：000050_user_kb_pins.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `tenant_id` | BIGINT | NOT NULL | 所属工作空间ID |
| `user_id` | VARCHAR(36) | NOT NULL | 置顶操作所属用户ID |
| `kb_id` | VARCHAR(36) | NOT NULL | 被置顶的知识库ID |
| `pinned_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 置顶时间，用于排序 |

**索引**：
- `idx_user_kb_pins_user_tenant_pinned_at` (`tenant_id, user_id, pinned_at DESC`)

