## 表：knowledge_processing_spans

> 业务含义：文档解析处理链路的追踪Span记录，支撑“文档解析追踪时间线”功能与失败排查
> 类型：基础设施表，非业务表
> 来源：000055_knowledge_processing_spans.up.sql, 000066_expand_knowledge_span_name.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | 自增主键 |
| `knowledge_id` | VARCHAR(64) | NOT NULL | 所属知识条目ID |
| `attempt` | INT | NOT NULL；默认 1 | 第几次解析尝试（重新解析会产生新的attempt） |
| `span_id` | VARCHAR(64) | NOT NULL | Span唯一标识 |
| `parent_span_id` | VARCHAR(64) | — | 父Span ID，构建调用树 |
| `name` | VARCHAR(64) | NOT NULL；后续变更：TYPE VARCHAR(255) | Span名称（如阶段/子阶段标识） |
| `kind` | VARCHAR(16) | NOT NULL | root / stage / subspan / generation |
| `status` | VARCHAR(16) | NOT NULL | pending/running/done/failed/skipped/cancelled |
| `input` | JSONB | — | 该Span的输入快照 |
| `output` | JSONB | — | 该Span的输出快照 |
| `metadata` | JSONB | — | 扩展元数据 |
| `error_code` | VARCHAR(64) | — | 失败错误码 |
| `error_message` | TEXT | — | 失败简要信息 |
| `error_detail` | TEXT | — | 失败详细信息 |
| `started_at` | TIMESTAMP WITH TIME ZONE | — | 开始时间 |
| `finished_at` | TIMESTAMP WITH TIME ZONE | — | 结束时间 |
| `duration_ms` | BIGINT | — | 耗时(ms) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_kpspan_knowledge_attempt` (`knowledge_id, attempt`)
- `idx_kpspan_status_started` (`status, started_at`)
- `idx_kpspan_parent` (`parent_span_id`)

