## 表：memory_subjects

> 业务含义：长期记忆的“记忆空间”主体：一个工作空间内一个调用主体（用户/IM用户/访客等）对应一个记忆空间，存有渲染好的常驻记忆文本块
> 来源：000084_memory.up.sql, 000094_memory_consistency.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 记忆空间ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `subject_id` | VARCHAR(512) | NOT NULL | 调用主体标识（Principal.StorageID()，涵盖IM用户、嵌入访客等非WeKnora账号） |
| `enabled` | BOOLEAN | NOT NULL；默认 true | 该主体是否开启记忆（个人开关，工作空间开关优先级更高） |
| `block_text` | TEXT | NOT NULL；默认 '' | 渲染好的常驻记忆文本块（画像/偏好等），每次写入后重新计算，读取时直接使用无需再排序聚合 |
| `block_updated_at` | TIMESTAMP WITH TIME ZONE | — | 常驻记忆块最近渲染时间 |
| `item_count` | INTEGER | NOT NULL；默认 0 | 当前活跃记忆条目数 |
| `last_extracted_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次后台抽取任务运行时间 |
| `extract_cursor` | TIMESTAMP WITH TIME ZONE | — | 旧版全局抽取水位游标（新逻辑改为按会话在memory_extraction_sessions记录进度，仅为兼容保留） |
| `pending_sessions` | JSONB | — | 旧版待处理会话队列（新worker不再增长此字段，仅为升级过渡保留） |
| `extract_scheduled_at` | TIMESTAMP WITH TIME ZONE | — | 标记当前是否已有一个抽取任务在途，避免同一时刻多轮触发重复入队 |
| `consolidated_at` | TIMESTAMP WITH TIME ZONE | — | 最近一次系统例行“记忆整理去重”执行时间 |
| `forced_consolidated_at` | TIMESTAMP WITH TIME ZONE | — | 用户手动触发“整理记忆”的时间（与例行整理使用独立时钟，互不影响频率限制） |
| `extraction_state` | JSONB | — | 抽取任务的分布式worker租约状态（lease_id/lease_until） |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_memory_subjects_scope` (`tenant_id, subject_id`) [UNIQUE]

