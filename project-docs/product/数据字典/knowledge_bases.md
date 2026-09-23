## 表：knowledge_bases

> 业务含义：知识库主表：一个知识库对应一套分块/向量化/存储/FAQ/Wiki等配置，是知识组织的顶层容器
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000004_drop_vlm_model_id.up.sql, 000014_storage_provider_config.up.sql, 000016_add_kb_pinned.up.sql, 000031_add_asr_config.up.sql, 000036_kb_vector_store_id.up.sql, 000037_wiki_and_indexing.up.sql, 000043_tenant_rbac.up.sql, 000068_storage_backends.up.sql, 000080_knowledge_base_auto_tag_config.up.sql, 000101_knowledge_profiles.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 知识库ID |
| `name` | VARCHAR(255) | NOT NULL | 知识库名称 |
| `description` | TEXT | — | 知识库人工填写的描述 |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `chunking_config` | JSONB | NOT NULL；默认 '{"chunk_size": 512 | 文档切分配置（chunk_size/overlap/分隔符/父子分块/解析引擎路由规则等） |
| `image_processing_config` | JSONB | NOT NULL；默认 '{"enable_multimodal": false | 图片处理配置（多模态开关及所用模型） |
| `embedding_model_id` | VARCHAR(64) | NOT NULL | 向量化所用模型ID |
| `summary_model_id` | VARCHAR(64) | NOT NULL | 摘要生成所用模型ID |
| `cos_config` | JSONB | NOT NULL；默认 '{}' | 旧版对象存储（COS等）配置，字段名沿用历史，已被 storage_provider_config/storage_backend_id 取代，仅兼容旧数据 |
| `vlm_config` | JSONB | NOT NULL；默认 '{}' | 视觉语言模型配置（用于图片OCR/图片描述生成） |
| `extract_config` | JSONB | 默认 NULL | 知识图谱抽取配置（是否启用、抽取的实体/关系类型等） |
| `is_temporary` | BOOLEAN | NOT NULL；默认 false | Whether this knowledge base is temporary (ephemeral) and should be hidden from UI |
| `type` | VARCHAR(32) | NOT NULL；默认 'document' | 知识库类型：document=文档型，faq=问答对型，wiki=Wiki型 |
| `faq_config` | JSONB | — | FAQ类知识库特有配置：索引模式(仅问题/问题+答案)、相似问索引方式 |
| `question_generation_config` | JSONB | — | 文档知识库的问题生成配置：是否为每个分块自动生成问题以提升召回 |
| `storage_provider_config` | JSONB | 默认 NULL | 知识库绑定的存储服务商选择（local/minio/cos/tos/s3/oss/ks3/obs），凭证仍在租户级配置 |
| `is_pinned` | BOOLEAN | NOT NULL；默认 false | 遗留字段：是否置顶，已被 user_kb_pins 表按用户维度的置顶替代，不再读写 |
| `pinned_at` | TIMESTAMP WITH TIME ZONE | — | 遗留字段：置顶时间，同上已废弃不再使用 |
| `asr_config` | JSONB | — | ASR (Automatic Speech Recognition) configuration: {"enabled": bool, "model_id": string, "language": string} |
| `vector_store_id` | VARCHAR(36) | — | References vector_stores.id. NULL means tenant default (env store derived from RETRIEVE_DRIVER). |
| `wiki_config` | JSONB | — | Wiki configuration: {"auto_ingest": bool, "synthesis_model_id": string, "wiki_language": string, "max_pages_per_ingest": int} |
| `indexing_strategy` | JSONB | — | Indexing pipelines strategy: {"vector_enabled": bool, "keyword_enabled": bool, "wiki_enabled": bool, "graph_enabled": bool} |
| `creator_id` | VARCHAR(36) | — | 知识库创建者用户ID，用于RBAC下“贡献者仅可编辑自己创建的资源” |
| `storage_backend_id` | VARCHAR(36) | — | 绑定的具体存储后端实例ID，指向 storage_backends.id |
| `auto_tag_config` | JSONB | — | 文档自动打标签配置：是否启用、使用的模型、单文档最多打几个标签 |
| `profile_config` | JSONB | — | 知识库描述自动生成配置：是否启用、使用的模型、自定义生成指引 |
| `generated_profile` | JSONB | — | 系统自动生成的知识库画像（一句话简介、合并主题词、典型问题样例及生成时的聚合快照哈希） |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_knowledge_bases_tenant_id` (`tenant_id`)
- `idx_knowledge_bases_tenant_vector_store` (`tenant_id, vector_store_id`)
- `idx_knowledge_bases_tenant_creator` (`tenant_id, creator_id`)
- `idx_knowledge_bases_storage_backend` (`tenant_id, storage_backend_id`)

