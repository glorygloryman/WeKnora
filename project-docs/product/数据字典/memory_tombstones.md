## 表：memory_tombstones

> 业务含义：用户主动要求“忘记”的记忆的墓碑记录：仅保存指纹哈希不保存原文，防止后台抽取任务从同一条消息再次生成相同记忆
> 来源：000084_memory.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记录ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `subject_id` | VARCHAR(512) | NOT NULL | 所属记忆空间的主体标识 |
| `topic` | VARCHAR(255) | NOT NULL；默认 '' | 被遗忘陈述的主题名 |
| `fingerprint` | VARCHAR(64) | NOT NULL | 被遗忘陈述归一化后的哈希指纹（不存原文） |
| `source_message_id` | VARCHAR(36) | — | 被拒绝记忆所源自的消息ID，防止同一消息被重新措辞后再次抽取通过 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |

**索引**：
- `idx_memory_tombstones_scope` (`tenant_id, subject_id`)
- `idx_mem_tomb_fp` (`tenant_id, subject_id, fingerprint`) [UNIQUE]

