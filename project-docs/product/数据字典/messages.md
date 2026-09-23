## 表：messages

> 业务含义：会话中的单条消息（用户提问或助手回答），承载检索引用、Agent执行步骤、附件产物与用量统计
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000005_mentioned_items.up.sql, 000015_add_is_fallback.up.sql, 000019_add_agent_duration_ms.up.sql, 000020_add_message_knowledge_id.up.sql, 000022_message_images.up.sql, 000025_message_channel.up.sql, 000027_message_rendered_content.up.sql, 000034_add_attachments.up.sql, 000067_question_suggestions.up.sql, 000081_message_artifacts.up.sql, 000084_memory.up.sql, 000085_message_usage.up.sql, 000097_session_fork.up.sql, 000105_message_context_checkpoint.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 消息ID |
| `request_id` | VARCHAR(36) | NOT NULL | 所属请求ID（一问一答共享，用于分组检索历史） |
| `session_id` | VARCHAR(36) | NOT NULL | 所属会话ID |
| `role` | VARCHAR(50) | NOT NULL | 消息角色：user/assistant/system |
| `content` | TEXT | NOT NULL | 消息文本内容 |
| `knowledge_references` | JSONB | NOT NULL；默认 '[]' | 该回答引用的知识分块列表 |
| `agent_steps` | JSONB | 默认 NULL | Agent execution steps (reasoning process and tool calls) |
| `is_completed` | BOOLEAN | NOT NULL；默认 false | 消息生成是否已完成 |
| `mentioned_items` | JSONB | 默认 '[]' | Stores @mentioned knowledge bases and files (id, name, type) when user sends a message |
| `is_fallback` | BOOLEAN | 默认 FALSE | 是否为兜底回复（未命中知识库匹配） |
| `agent_duration_ms` | BIGINT | 默认 0 | Agent从查询开始到回答开始的总耗时(ms) |
| `knowledge_id` | VARCHAR(36) | — | 关联的对话历史知识库中的Knowledge条目ID（当消息被索引为可检索段落时） |
| `images` | JSONB | 默认 '[]' | 消息中附带的图片（含OCR/图片描述文本），用户消息使用 |
| `channel` | VARCHAR(50) | NOT NULL；默认 '' | Source channel of the message: web, api, im, etc. |
| `rendered_content` | TEXT | NOT NULL；默认 '' | Full RAG-augmented user message sent to LLM, preserving retrieval context across turns |
| `attachments` | JSONB | 默认 '[]'::jsonb | 消息附带的文件（文档、音频等）解析结果 |
| `agent_id` | VARCHAR(36) | NOT NULL；默认 '' | 该轮实际使用的Agent ID（区别于会话级“上次请求状态”，单条消息保持稳定） |
| `agent_tenant_id` | INTEGER | NOT NULL；默认 0 | 解析共享Agent所用模型/知识库时的有效/来源租户ID |
| `model_id` | VARCHAR(64) | NOT NULL；默认 '' | 该轮实际请求/生效的对话模型ID |
| `execution_context` | JSONB | NOT NULL；默认 '{}'::jsonb | 生成后续追问建议等派生体验所需的非敏感请求快照（KB/标签/MCP范围、语言等） |
| `artifacts` | JSONB | 默认 '[]'::jsonb | 本轮沙箱脚本生成并已持久化的文件列表（仅助手消息，实际存储于 message_artifacts 表） |
| `used_memories` | JSONB | — | 本轮回答实际注入使用的长期记忆条目列表，供前端展示及“删除该记忆”操作 |
| `usage` | JSONB | — | 本轮（含多次LLM调用）聚合的Token用量统计 |
| `sandbox_checkpoint` | JSONB | — | 本轮助手消息在会话沙箱/workspace中产生的git提交（sandbox_id+commit_sha），可作为Fork起点 |
| `context_checkpoint` | JSONB | — | Agent compaction summary covering this turn and every turn before it |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_messages_session_id` (`session_id`)
- `idx_messages_agent_steps` (`agent_steps`)
- `idx_messages_knowledge_id` (`knowledge_id`)
- `idx_messages_agent_id` (`agent_id`)
- `idx_messages_session_created_id` (`session_id, created_at DESC, id DESC`)

