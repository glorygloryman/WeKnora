## 表：tenants

> 业务含义：工作空间（租户）主表：存储空间的检索引擎、Agent/上下文/对话/存储/记忆等全局默认配置，是多租户隔离的根实体
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000013_engine_configs.up.sql, 000018_extend_tenant_api_key.up.sql, 000020_add_message_knowledge_id.up.sql, 000035_add_credentials.up.sql, 000064_principal_model.up.sql, 000065_tenant_api_keys.up.sql, 000068_storage_backends.up.sql, 000084_memory.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | SERIAL | PRIMARY KEY | 租户ID，自增主键 |
| `name` | VARCHAR(255) | NOT NULL | 租户（工作空间）名称 |
| `description` | TEXT | — | 租户描述 |
| `retriever_engines` | JSONB | NOT NULL；默认 '[]' | 该租户启用的检索引擎列表（JSON数组） |
| `status` | VARCHAR(50) | 默认 'active' | 租户状态，默认 active=启用 |
| `business` | VARCHAR(255) | NOT NULL | 租户所属业务线/用途标识 |
| `storage_quota` | BIGINT | NOT NULL；默认 10737418240 | 默认10GB配额(Bytes) |
| `storage_used` | BIGINT | NOT NULL；默认 0 | 已使用的存储空间(Bytes) |
| `agent_config` | JSONB | 默认 NULL；后续变更：TYPE JSONB USING agent_config::jsonb | Tenant-level agent configuration in JSON format |
| `context_config` | JSONB | — | Global Context configuration for this tenant (default for all sessions) |
| `conversation_config` | JSONB | — | Global Conversation configuration for this tenant (default for normal mode sessions) |
| `web_search_config` | JSONB | 默认 NULL | Web search configuration for the tenant |
| `parser_engine_config` | JSONB | 默认 NULL | 租户级文档解析引擎默认配置（按文件类型路由解析器） |
| `storage_engine_config` | JSONB | 默认 NULL | 租户级对象存储引擎默认配置（旧版单一存储写法，逐步被 storage_backends 多实例替代） |
| `chat_history_config` | JSONB | — | 对话历史知识库（可检索的历史消息索引）配置 |
| `retrieval_config` | JSONB | — | 租户级检索策略默认配置 |
| `credentials` | JSONB | 默认 NULL | 租户级第三方凭证集合（加密存储） |
| `api_principal_config` | JSONB | — | API Key 身份主体（principal）模式相关配置 |
| `default_storage_backend_id` | VARCHAR(36) | — | 默认使用的存储后端实例ID，指向 storage_backends.id |
| `memory_config` | JSONB | — | 长期记忆功能的工作空间级开关与参数：enabled/write_mode(explicit_only\|auto)/extract_model_id/max_items 等 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_tenants_api_key` (`api_key`)
- `idx_tenants_status` (`status`)
- `idx_tenants_agent_config` (`agent_config`)

