## 表：chunk_revisions

> 业务含义：分块内容被覆盖前的历史版本快照，支撑分块编辑的“版本历史+回滚”功能
> 来源：000078_chunk_editing_and_custom_metadata.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 快照ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `knowledge_id` | VARCHAR(36) | NOT NULL | 所属知识条目ID |
| `chunk_id` | VARCHAR(36) | NOT NULL | 所属分块ID |
| `revision` | INT | NOT NULL | 该快照对应的修订版本号 |
| `content` | TEXT | NOT NULL；默认 '' | 该版本内容 |
| `is_enabled` | BOOLEAN | NOT NULL；默认 TRUE | 该版本的启用状态 |
| `editor_id` | VARCHAR(64) | NOT NULL；默认 '' | 产生该版本的操作者标识 |
| `edit_source` | VARCHAR(16) | NOT NULL；默认 'user' | 编辑来源，默认user用户手工编辑 |
| `edited_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 该版本产生时间 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 该快照写入数据库的时间 |

**索引**：
- `idx_chunk_revisions_chunk_revision` (`chunk_id, revision`) [UNIQUE]
- `idx_chunk_revisions_tenant_chunk` (`tenant_id, chunk_id`)

