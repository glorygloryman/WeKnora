## 表：resource_bindings

> 业务含义：资源与其所有者（知识条目/消息/临时文档等）之间的引用关系表，实现“一份文件多处引用、任一处删除不影响其他”的共享语义
> 类型：基础设施表，非业务表
> 来源：000069_resource_registry.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 绑定记录ID |
| `resource_id` | VARCHAR(36) | NOT NULL；FK→resources.id ON DELETE CASCADE | 被引用的资源ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `owner_type` | VARCHAR(32) | NOT NULL | 所有者类型：knowledge知识条目/message消息/temporary_document临时文档 |
| `owner_id` | VARCHAR(64) | NOT NULL | 所有者对象ID |
| `relation` | VARCHAR(32) | NOT NULL；默认 'attachment' | 引用关系：source_file源文件/extracted_image提取的图片/artifact生成产物/attachment附件 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |

**索引**：
- `idx_resource_bindings_unique` (`resource_id, owner_type, owner_id, relation`) [UNIQUE]
- `idx_resource_bindings_owner` (`tenant_id, owner_type, owner_id`)

**外键**：
- `resource_id` → resources.id ON DELETE CASCADE

