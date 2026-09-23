## 表：task_dead_letters

> 业务含义：异步任务失败归档表：重试耗尽后的任务快照，供运维排查与手动补救
> 类型：基础设施表，非业务表
> 来源：000041_task_queue_and_wiki_indexes.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增行ID |
| `tenant_id` | BIGINT | NOT NULL | Tenant scope mirrored from the original task payload (best-effort) |
| `task_type` | VARCHAR(64) | NOT NULL | 任务类型标识（如 summary:generation） |
| `scope` | VARCHAR(32) | NOT NULL | Logical scope, mirrors task_pending_ops.scope，无法识别时为unknown |
| `scope_id` | VARCHAR(64) | NOT NULL | 作用域内标识，如kbID |
| `related_id` | VARCHAR(64) | NOT NULL；默认 '' | Optional secondary identifier. Wiki ingest puts knowledge_id here so retract/ingest dead letters cluster around the source document. |
| `payload` | JSONB | NOT NULL | Raw task payload (asynq.Task.Payload) at the time of failure. Allows manual requeue via SQL + asynq.Client.Enqueue. |
| `last_error` | TEXT | NOT NULL；默认 '' | String form of the error that caused the final retry to fail. Long stack traces are kept verbatim. |
| `fail_count` | INT | NOT NULL | 记录写入时的累计尝试次数 |
| `failed_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 服务端写入（最终失败判定）时间 |

**索引**：
- `idx_task_dead_letters_scope` (`scope, scope_id, failed_at DESC`)
- `idx_task_dead_letters_tenant` (`tenant_id, failed_at DESC`)
- `idx_task_dead_letters_task_type` (`task_type, failed_at DESC`)

