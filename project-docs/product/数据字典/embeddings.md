## 表：embeddings

> 业务含义：向量检索的旧版一体化存储表（PostgreSQL内置pgvector方案）：文本内容+向量+来源引用
> 来源：000002_embeddings.up.sql, 000007_embeddings_tag_id.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | SERIAL | PRIMARY KEY | 自增主键 |
| `source_id` | VARCHAR(64) | NOT NULL | 来源对象ID（如chunk_id） |
| `source_type` | INTEGER | NOT NULL | 来源对象类型编码 |
| `chunk_id` | VARCHAR(64) | — | 关联的分块ID |
| `knowledge_id` | VARCHAR(64) | — | 关联的知识条目ID |
| `knowledge_base_id` | VARCHAR(64) | — | 关联的知识库ID |
| `content` | TEXT | — | 被向量化的文本内容（冗余存储便于检索直接返回） |
| `dimension` | INTEGER | NOT NULL | 向量维度 |
| `embedding` | halfvec | — | 向量本体（halfvec半精度向量类型，供pgvector近似检索） |
| `is_enabled` | BOOLEAN | 默认 TRUE | 是否启用参与检索 |
| `tag_id` | VARCHAR(36) | — | 关联标签ID |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `embeddings_unique_source` (`source_id, source_type`) [UNIQUE]
- `embeddings_search_idx` (`id, knowledge_base_id, content, knowledge_id, chunk_id`)
- `embeddings_embedding_idx_3584` (`(embedding::halfvec(3584`)
- `embeddings_embedding_idx_798` (`(embedding::halfvec(798`)
- `idx_embeddings_is_enabled` (`is_enabled`)
- `idx_embeddings_knowledge_base_id` (`knowledge_base_id`)
- `idx_embeddings_tag_id` (`tag_id`)
- `embeddings_embedding_idx_1024` (`(embedding::halfvec(1024`)

