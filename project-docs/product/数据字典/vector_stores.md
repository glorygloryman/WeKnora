## 表：vector_stores

> 业务含义：租户可配置的向量数据库实例注册表：支持ES/Qdrant/Milvus/Weaviate/腾讯VectorDB/Doris/OpenSearch等多引擎多实例
> 来源：000032_vector_stores.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 向量库实例ID |
| `name` | VARCHAR(255) | NOT NULL | 实例名称，如 elasticsearch-hot |
| `engine_type` | VARCHAR(50) | NOT NULL | 引擎类型：elasticsearch/qdrant/milvus/weaviate/doris/tencent_vectordb/opensearch等 |
| `connection_config` | JSONB | NOT NULL；默认 '{}' | 连接参数（地址、账号密码/APIKey均加密存储、TLS开关等，因引擎而异） |
| `index_config` | JSONB | NOT NULL；默认 '{}' | 索引/集合配置（分片数、副本数、HNSW参数等，引擎相关，为空则用引擎默认值） |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_vector_stores_name_tenant` (`name, tenant_id`) [UNIQUE]
- `idx_vector_stores_tenant_id` (`tenant_id`)
- `idx_vector_stores_engine_type` (`engine_type`)
- `idx_vector_stores_deleted_at` (`deleted_at`)

