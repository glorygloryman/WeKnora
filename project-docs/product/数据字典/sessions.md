## 表：sessions

> 业务含义：对话会话主表：一次用户与Agent的多轮对话上下文及其检索/召回策略参数
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000006_custom_agents.up.sql, 000039_session_user_id_and_pin.up.sql, 000064_principal_model.up.sql, 000083_session_sandbox_config.up.sql, 000097_session_fork.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 会话ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `title` | VARCHAR(255) | — | 会话标题 |
| `description` | TEXT | — | 会话描述（内部也用作特殊会话类型的隐藏标记前缀，如skill_maintenance:） |
| `knowledge_base_id` | VARCHAR(36) | — | 会话默认关联的知识库ID |
| `max_rounds` | INTEGER | NOT NULL；默认 5 | 多轮对话保留轮数 |
| `enable_rewrite` | BOOLEAN | NOT NULL；默认 true | 是否启用多轮问题改写 |
| `fallback_strategy` | VARCHAR(255) | NOT NULL；默认 'fixed' | 兜底策略：fixed=固定话术，model=模型生成兜底回复 |
| `fallback_response` | TEXT | NOT NULL；默认 '很抱歉，我暂时无法回答这个问题。' | 固定兜底回复文案 |
| `keyword_threshold` | FLOAT | NOT NULL；默认 0.5 | 关键词召回相似度阈值 |
| `vector_threshold` | FLOAT | NOT NULL；默认 0.5 | 向量召回相似度阈值 |
| `rerank_model_id` | VARCHAR(64) | — | 重排序模型ID |
| `embedding_top_k` | INTEGER | NOT NULL；默认 10 | 向量召回TopK |
| `rerank_top_k` | INTEGER | NOT NULL；默认 10 | 重排序后保留TopK |
| `rerank_threshold` | FLOAT | NOT NULL；默认 0.65 | 重排序分数阈值 |
| `summary_model_id` | VARCHAR(64) | — | 会话摘要所用模型ID |
| `summary_parameters` | JSONB | NOT NULL；默认 '{}' | 摘要生成的模型调用参数（温度、topK、prompt等） |
| `agent_config` | JSONB | 默认 NULL | Session-level agent configuration in JSON format |
| `context_config` | JSONB | 默认 NULL | LLM context management configuration (separate from message storage) |
| `agent_id` | VARCHAR(36) | — | 会话使用的自定义Agent ID |
| `user_id` | VARCHAR(36) | 后续变更：TYPE VARCHAR(512) | 会话归属用户/主体标识：WeKnora用户UUID，或API外部用户/嵌入访客等派生主体ID |
| `is_pinned` | BOOLEAN | NOT NULL；默认 FALSE | 是否在会话列表中置顶 |
| `pinned_at` | TIMESTAMP WITH TIME ZONE | — | 置顶时间 |
| `sandbox_config_id` | VARCHAR(36) | 默认 NULL | 该会话当前存活沙箱所绑定的沙箱配置ID，空表示当前无存活沙箱 |
| `parent_session_id` | VARCHAR(36) | — | 分支来源的父会话ID（会话Fork功能），为空表示普通会话 |
| `forked_from_message_id` | VARCHAR(36) | — | Fork时的分叉起点消息ID（父会话中的用户或助手消息） |
| `fork_bootstrap` | JSONB | — | Fork会话的一次性沙箱引导指令：从哪个快照启动、回滚到哪个commit，消费一次后失效 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_sessions_tenant_id` (`tenant_id`)
- `idx_sessions_agent_config` (`agent_config`)
- `idx_sessions_context_config` (`context_config`)
- `idx_sessions_agent_id` (`agent_id`)
- `idx_sessions_tenant_user_pin` (`tenant_id, user_id, is_pinned DESC, pinned_at DESC, updated_at DESC`)
- `idx_sessions_parent_session_id` (`parent_session_id`)
- `idx_sessions_unconsumed_fork` (`(fork_bootstrap ->> 'snapshot_id'`)

