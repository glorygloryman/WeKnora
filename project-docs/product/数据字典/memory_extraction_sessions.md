## 表：memory_extraction_sessions

> 业务含义：长期记忆后台抽取任务按会话维度的进度台账：记录每个会话抽取到的消息游标及失败重试信息，替代旧版全局游标
> 类型：基础设施表，非业务表
> 来源：000094_memory_consistency.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID（联合主键） |
| `subject_id` | VARCHAR(512) | NOT NULL | 所属记忆空间主体标识（联合主键） |
| `session_id` | VARCHAR(36) | NOT NULL | 被抽取的会话ID（联合主键） |
| `revision` | BIGINT | NOT NULL；默认 0 | 乐观锁版本号 |
| `cursor_at` | TIMESTAMP WITH TIME ZONE | — | 已抽取到的消息时间游标 |
| `cursor_id` | VARCHAR(36) | NOT NULL；默认 '' | 已抽取到的消息ID（配合cursor_at打破同时间戳的顺序歧义） |
| `pending` | BOOLEAN | NOT NULL；默认 false | 是否仍有待处理的抽取工作 |
| `failure_count` | INTEGER | NOT NULL；默认 0 | 连续失败次数 |
| `failure_code` | VARCHAR(64) | NOT NULL；默认 '' | 最近一次失败的错误码 |
| `failed_from_at` | TIMESTAMP WITH TIME ZONE | — | 本次失败重试窗口的起始时间游标 |
| `failed_from_id` | VARCHAR(36) | NOT NULL；默认 '' | 本次失败重试窗口的起始消息ID |
| `failed_to_at` | TIMESTAMP WITH TIME ZONE | — | 本次失败重试窗口的结束时间游标 |
| `failed_to_id` | VARCHAR(36) | NOT NULL；默认 '' | 本次失败重试窗口的结束消息ID |
| `failed_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次失败时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | 审计字段：更新时间 |

**索引**：
- `idx_memory_extraction_pending` (`tenant_id, subject_id, pending, updated_at, session_id`)

