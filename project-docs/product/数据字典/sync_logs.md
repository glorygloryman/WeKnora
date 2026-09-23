## 表：sync_logs

> 业务含义：数据源每次同步任务的执行记录：处理条目统计与错误明细
> 来源：000029_datasource_tables.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 同步日志ID |
| `data_source_id` | VARCHAR(36) | NOT NULL；FK→data_sources.id ON DELETE CASCADE | 关联的数据源ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `status` | VARCHAR(32) | NOT NULL | 同步状态：running/success/partial/failed/canceled |
| `started_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 开始时间 |
| `finished_at` | TIMESTAMP | — | 结束时间 |
| `items_total` | INT | 默认 0 | 本次同步处理条目总数 |
| `items_created` | INT | 默认 0 | 新建条目数 |
| `items_updated` | INT | 默认 0 | 更新条目数 |
| `items_deleted` | INT | 默认 0 | 删除条目数 |
| `items_skipped` | INT | 默认 0 | 跳过（无变化）条目数 |
| `items_failed` | INT | 默认 0 | 失败条目数 |
| `error_message` | TEXT | — | 同步失败时的错误信息 |
| `result` | JSONB | — | 同步详细结果（含失败样例、下次游标等） |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_sync_logs_data_source_id` (`data_source_id`)
- `idx_sync_logs_tenant_id` (`tenant_id`)
- `idx_sync_logs_status` (`status`)
- `idx_sync_logs_started_at` (`started_at`)

**外键**：
- `data_source_id` → data_sources.id ON DELETE CASCADE

