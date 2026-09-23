## 表：temporary_documents

> 业务含义：会话级临时附件文档：用户在对话中上传的、有效期有限的文件及其解析产物，独立于正式知识库
> 来源：000070_temporary_documents.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 临时文档ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `session_id` | VARCHAR(36) | NOT NULL | 所属会话ID |
| `resource_ref` | TEXT | NOT NULL | 关联的resources.handle等内部引用 |
| `file_name` | VARCHAR(1024) | NOT NULL | 原始文件名 |
| `file_type` | VARCHAR(32) | NOT NULL | 文件类型 |
| `mime_type` | VARCHAR(255) | NOT NULL；默认 '' | MIME类型 |
| `file_size` | BIGINT | NOT NULL | 文件大小(字节) |
| `status` | VARCHAR(16) | NOT NULL；默认 'uploaded' | 处理状态：uploaded已上传/processing解析中/ready已就绪/failed失败 |
| `content` | TEXT | NOT NULL；默认 '' | 解析出的全文文本 |
| `chunks` | JSONB | NOT NULL；默认 '[]'::jsonb | 解析后的分块列表（供本轮对话按需选用部分分块作为上下文） |
| `image_refs` | JSONB | NOT NULL；默认 '[]'::jsonb | 解析出的图片引用列表 |
| `metadata` | JSONB | NOT NULL；默认 '{}'::jsonb | 扩展元数据 |
| `processing_options` | JSONB | NOT NULL；默认 '{}'::jsonb | 解析选项（如是否启用图片理解、OCR页数上限等） |
| `token_count` | INTEGER | NOT NULL；默认 0 | 解析文本的近似token数 |
| `chunk_count` | INTEGER | NOT NULL；默认 0 | 分块数量 |
| `error_message` | TEXT | NOT NULL；默认 '' | 解析失败时的错误信息 |
| `expires_at` | TIMESTAMP | NOT NULL | 过期时间，到期后清理 |
| `started_at` | TIMESTAMP | — | 开始解析时间 |
| `ready_at` | TIMESTAMP | — | 解析就绪时间 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_temporary_documents_scope` (`tenant_id, session_id`)
- `idx_temporary_documents_status` (`status`)
- `idx_temporary_documents_expires` (`expires_at`)

