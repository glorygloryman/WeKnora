## 表：memory_item_embeddings

> 业务含义：长期记忆条目的向量表示，独立建表避免高频列表查询携带向量数据，仅语义召回时读取
> 来源：000084_memory.up.sql, 000095_memory_vector_search.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `item_id` | VARCHAR(36) | PRIMARY KEY | 对应的memory_items.id |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `subject_id` | VARCHAR(512) | NOT NULL | 所属记忆空间的主体标识 |
| `model_id` | VARCHAR(64) | NOT NULL；默认 '' | 产生该向量的模型ID（不同模型向量不可比较） |
| `dims` | INTEGER | NOT NULL；默认 0 | 向量维度 |
| `vector` | BYTEA | — | 旧版向量存储字段（小端float32二进制），逐步由embedding列取代 |
| `embedding` | halfvec | — | 向量本体（halfvec类型，供pgvector近似检索） |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_mem_emb_scope` (`tenant_id, subject_id`)
- `idx_mem_emb_search` (`tenant_id, subject_id, model_id, dims`)

