## 表：wiki_page_issues

> 业务含义：Wiki页面质量问题上报表（如内容矛盾、链接失效等），供人工/Agent审阅修复
> 来源：000037_wiki_and_indexing.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 问题记录ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `slug` | VARCHAR(255) | NOT NULL | 问题所属页面slug |
| `issue_type` | VARCHAR(50) | NOT NULL | 问题类型（如内容冲突、过期信息等） |
| `description` | TEXT | NOT NULL | 问题描述 |
| `suspected_knowledge_ids` | JSONB | — | 疑似相关的来源知识条目ID列表 |
| `status` | VARCHAR(20) | NOT NULL；默认 'pending' | 处理状态，默认pending待处理 |
| `reported_by` | VARCHAR(100) | NOT NULL | 上报者标识（可为Agent或用户） |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_wiki_page_issues_tenant_id` (`tenant_id`)
- `idx_wiki_page_issues_knowledge_base_id` (`knowledge_base_id`)
- `idx_wiki_page_issues_slug` (`slug`)
- `idx_wiki_page_issues_status` (`status`)

