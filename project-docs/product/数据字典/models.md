## 表：models

> 业务含义：租户下配置的 AI 模型清单：Embedding/Rerank/对话(KnowledgeQA)/多模态(VLLM)/语音识别(ASR) 等各类模型的连接参数
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000052_models_managed_by.up.sql, 000057_models_display_name.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(64) | PRIMARY KEY；默认 uuid_generate_v4() | 模型ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL | 模型内部名称（调用时使用） |
| `display_name` | VARCHAR(255) | NOT NULL；默认 '' | 模型展示名称（仅用于界面显示） |
| `type` | VARCHAR(50) | NOT NULL | 模型类型：Embedding=向量化/Rerank=重排/KnowledgeQA=对话问答/VLLM=多模态视觉/ASR=语音识别 |
| `source` | VARCHAR(50) | NOT NULL | 模型供应商来源，如 local/remote/openai/deepseek/aliyun/zhipu/volcengine/hunyuan/minimax/gemini/siliconflow/litellm 等20+种 |
| `description` | TEXT | — | 模型描述 |
| `parameters` | JSONB | NOT NULL | 模型连接参数（JSON，含 base_url、加密存储的 api_key、embedding维度、上下文窗口、并发限制等） |
| `is_default` | BOOLEAN | NOT NULL；默认 false | 是否为该类型的默认模型 |
| `status` | VARCHAR(50) | NOT NULL；默认 'active' | 模型状态：active=可用，downloading=下载中，download_failed=下载失败 |
| `is_builtin` | BOOLEAN | NOT NULL；默认 false | 是否为内置模型（对所有租户可见） |
| `managed_by` | VARCHAR(32) | NOT NULL；默认 '' | 该行生命周期归属：空=手工创建，yaml=由 config/builtin_models.yaml 声明式管理并自动同步 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_models_type` (`type`)
- `idx_models_source` (`source`)
- `idx_models_is_builtin` (`is_builtin`)
- `idx_models_managed_by_yaml` (`managed_by`)

