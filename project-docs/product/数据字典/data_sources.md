## 表：data_sources

> 业务含义：外部数据源连接配置：飞书/Notion/GitLab/语雀/钉钉文档/RSS等自动同步知识的数据源定义
> 来源：000029_datasource_tables.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 数据源ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 同步目标知识库ID |
| `name` | VARCHAR(255) | NOT NULL | 数据源名称 |
| `type` | VARCHAR(50) | NOT NULL | 连接器类型：feishu/lark/feishu_drive/notion/confluence/yuque/github/dingtalk/gitlab/ima/rss等 |
| `config` | JSONB | — | 加密存储的连接配置（凭证、选中资源ID、连接器专属设置） |
| `sync_schedule` | VARCHAR(100) | — | 定时同步的Cron表达式 |
| `sync_mode` | VARCHAR(20) | 默认 'incremental' | 同步模式：incremental增量（推荐）/full全量 |
| `status` | VARCHAR(32) | 默认 'active' | 数据源状态：active/paused/error/deleted |
| `conflict_strategy` | VARCHAR(32) | 默认 'overwrite' | 冲突解决策略：overwrite覆盖/skip跳过 |
| `sync_deletions` | BOOLEAN | 默认 true | 是否同步源端的删除操作 |
| `last_sync_at` | TIMESTAMP | — | 最近一次成功同步时间 |
| `last_sync_cursor` | JSONB | — | 增量同步游标/断点状态（连接器相关） |
| `last_sync_result` | JSONB | — | 最近一次同步结果摘要 |
| `error_message` | TEXT | — | status为error时的错误信息 |
| `sync_log_retention_days` | INT | 默认 30 | 同步日志保留天数，默认30 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_data_sources_tenant_id` (`tenant_id`)
- `idx_data_sources_knowledge_base_id` (`knowledge_base_id`)
- `idx_data_sources_type` (`type`)
- `idx_data_sources_status` (`status`)
- `idx_data_sources_deleted_at` (`deleted_at`)

