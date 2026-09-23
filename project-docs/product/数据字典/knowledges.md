## 表：knowledges

> 业务含义：知识条目（文档/URL/FAQ导入/手写Markdown等）主表：记录文件元信息、解析状态与生成的摘要/画像
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000009_add_last_faq_import_result.up.sql, 000025_message_channel.up.sql, 000056_knowledge_pending_subtasks.up.sql, 000058_expand_knowledge_source.up.sql, 000063_knowledge_multi_tags.up.sql, 000078_chunk_editing_and_custom_metadata.up.sql, 000079_knowledge_folder_path.up.sql, 000101_knowledge_profiles.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 知识条目ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `type` | VARCHAR(50) | NOT NULL | 知识条目类型（如普通文档、manual=手写Markdown、faq=问答对） |
| `title` | VARCHAR(255) | NOT NULL | 标题 |
| `description` | TEXT | — | 描述 |
| `source` | VARCHAR(2048) | NOT NULL；后续变更：TYPE VARCHAR(2048) | 来源标识：URL地址（url类型）或 manual（手写类型）等 |
| `parse_status` | VARCHAR(50) | NOT NULL；默认 'unprocessed' | 解析状态：pending待处理/processing解析中/finalizing主解析完成后台增强中/completed全部完成/failed失败/deleting删除中/cancelled已取消 |
| `enable_status` | VARCHAR(50) | NOT NULL；默认 'enabled' | 启用状态，控制该条目是否参与检索 |
| `embedding_model_id` | VARCHAR(64) | — | 该条目使用的向量化模型ID |
| `file_name` | VARCHAR(255) | — | 原始文件名 |
| `file_type` | VARCHAR(50) | — | 文件类型/扩展名 |
| `file_size` | BIGINT | — | 文件大小（字节） |
| `file_path` | TEXT | — | 文件存储路径（provider://path 形式） |
| `file_hash` | VARCHAR(64) | — | 文件内容哈希，用于去重 |
| `storage_size` | BIGINT | NOT NULL；默认 0 | 存储大小(Byte) |
| `metadata` | JSONB | — | 内部摄取过程元数据（外部数据源external_id、迁移恢复标记、处理选项覆盖等） |
| `processed_at` | TIMESTAMP WITH TIME ZONE | — | 解析完成时间 |
| `error_message` | TEXT | — | 解析失败时的错误信息 |
| `summary_status` | VARCHAR(32) | 默认 'none' | 摘要异步生成状态：none无需生成/pending待处理/processing生成中/completed已完成/failed失败 |
| `last_faq_import_result` | JSON | 默认 NULL | FAQ类型知识库最近一次批量导入的结果统计（仅FAQ类型使用） |
| `channel` | VARCHAR(50) | NOT NULL；默认 'web' | Source channel of the knowledge: web, api, browser_extension, wechat, etc. |
| `pending_subtasks_count` | INT | NOT NULL；默认 0 | 解析完成后仍在后台运行的增强子任务数（摘要/问题生成/图谱抽取），归零后状态转为completed |
| `custom_metadata` | JSONB | NOT NULL；默认 '{}'::JSONB | 用户自定义的描述性元数据（与内部metadata区分，供检索上下文展示） |
| `folder_path` | VARCHAR(1024) | NOT NULL；默认 '' | 该文档在知识库目录树中所属的相对文件夹路径，空串表示知识库根目录 |
| `profile` | JSONB | — | 系统为该文档生成的结构化画像：一句话概述(gist)/主题词(topics)/文档类型(doc_type)/典型问题 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_knowledges_tenant_id` (`tenant_id`)
- `idx_knowledges_base_id` (`knowledge_base_id`)
- `idx_knowledges_parse_status` (`parse_status`)
- `idx_knowledges_enable_status` (`enable_status`)
- `idx_knowledges_tag` (`tag_id`)
- `idx_knowledges_summary_status` (`summary_status`)
- `idx_knowledges_kb_metadata_external_id` (`knowledge_base_id, (metadata->>'external_id'`)
- `idx_knowledges_folder_path` (`tenant_id, knowledge_base_id, folder_path`)

