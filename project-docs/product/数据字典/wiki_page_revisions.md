## 表：wiki_page_revisions

> 业务含义：Wiki页面被覆盖前的历史版本快照，支撑“版本历史+行级Diff+一键回滚”功能
> 来源：000075_wiki_page_revisions.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 快照ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `page_id` | VARCHAR(36) | NOT NULL | 所属页面ID |
| `slug` | VARCHAR(255) | NOT NULL | 页面当时的slug |
| `version` | INT | NOT NULL | 该快照对应的版本号 |
| `title` | VARCHAR(512) | NOT NULL；默认 '' | 该版本标题 |
| `page_type` | VARCHAR(32) | NOT NULL；默认 'summary' | 该版本页面类型 |
| `status` | VARCHAR(32) | NOT NULL；默认 'published' | 该版本状态 |
| `content` | TEXT | NOT NULL；默认 '' | 该版本正文内容 |
| `summary` | TEXT | NOT NULL；默认 '' | 该版本摘要 |
| `aliases` | JSONB | 默认 '[]'::JSONB | 该版本别名列表 |
| `edit_source` | VARCHAR(16) | NOT NULL；默认 '' | 该版本作者类型：pipeline/agent/user/revert |
| `editor_id` | VARCHAR(64) | NOT NULL；默认 '' | 产生该版本的用户ID |
| `edited_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 该版本产生时间（原页面updated_at） |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 该快照写入数据库的时间 |

**索引**：
- `idx_wiki_page_revisions_page_version` (`page_id, version`) [UNIQUE]
- `idx_wiki_page_revisions_kb_slug` (`knowledge_base_id, slug`)

