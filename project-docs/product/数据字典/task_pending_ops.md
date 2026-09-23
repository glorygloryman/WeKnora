## 表：task_pending_ops

> 业务含义：通用持久化任务待处理队列（替代原Redis List方案），主要用于Wiki摄取等按批次消费的操作队列
> 类型：基础设施表，非业务表
> 来源：000041_task_queue_and_wiki_indexes.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增行ID，用于批次消费排序 |
| `tenant_id` | BIGINT | NOT NULL | Tenant scope mirrored from the enclosing object |
| `task_type` | VARCHAR(64) | NOT NULL | Free-form task identifier, e.g. "wiki:ingest" — should match an asynq task type when applicable. |
| `scope` | VARCHAR(32) | NOT NULL | Logical scope, e.g. "knowledge_base" / "knowledge" / "tenant". Read together with scope_id. |
| `scope_id` | VARCHAR(64) | NOT NULL | 队列作用域内的具体标识（如知识库ID） |
| `op` | VARCHAR(32) | NOT NULL | 操作类型，消费方自定义，如wiki的ingest/retract |
| `dedup_key` | VARCHAR(128) | NOT NULL；默认 '' | Optional service-defined key used by the consumer to de-duplicate equivalent ops within a single batch peek. Empty means no de-dup. |
| `payload` | JSONB | NOT NULL；默认 '{}'::JSONB | 操作载荷（JSON，消费方自定义schema） |
| `fail_count` | INT | NOT NULL；默认 0 | In-batch retry counter: the consumer increments it via IncrFailCount and dead-letters once it exceeds a service-defined cap. |
| `enqueued_at` | TIMESTAMPTZ | NOT NULL；默认 NOW() | 入队时间 |
| `claimed_at` | TIMESTAMPTZ | — | 预留字段：领取时间戳，当前版本未实际使用，为未来无锁并行消费预留 |

**索引**：
- `idx_task_pending_ops_scope` (`task_type, scope, scope_id, id`)
- `idx_task_pending_ops_tenant` (`tenant_id`)

