## 表：message_artifacts

> 业务含义：助手消息在沙箱中执行技能脚本产生并持久化的文件产物明细（如生成的Word/PPT/图表文件）
> 来源：000103_message_artifacts_table.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 产物记录ID |
| `session_id` | VARCHAR(36) | NOT NULL | 所属会话ID |
| `message_id` | VARCHAR(36) | NOT NULL | 所属消息ID |
| `position` | INTEGER | NOT NULL | 在该消息产物列表中的顺序位置，作为下载接口的寻址索引 |
| `url` | TEXT | NOT NULL；默认 '' | 持久化存储的访问URL（内部provider://路径） |
| `file_name` | TEXT | NOT NULL；默认 '' | 沙箱内的原始文件名 |
| `file_type` | VARCHAR(32) | NOT NULL；默认 '' | 文件扩展名 |
| `file_size` | BIGINT | NOT NULL；默认 0 | 文件大小(字节) |
| `content_hash` | VARCHAR(64) | NOT NULL；默认 '' | 持久化内容的SHA-256哈希，用于同一文件多次生成时的版本判定 |
| `source_path` | TEXT | NOT NULL；默认 '' | 沙箱内的绝对路径，用于比对差异 |
| `mod_time` | VARCHAR(64) | NOT NULL；默认 '' | 沙箱内文件的修改时间（RFC3339Nano文本，纳秒级精度用于比对是否变化） |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 CURRENT_TIMESTAMP | 审计字段：创建时间（WeKnora完成持久化的时间） |

**索引**：
- `idx_message_artifacts_message_position` (`message_id, position`) [UNIQUE]
- `idx_message_artifacts_session_created` (`session_id, created_at`)

