## 表：wiki_pages

> 业务含义：Wiki模式下由Agent从原始文档蒸馏生成的互链Markdown知识页面，是自维护知识库/知识图谱的核心实体
> 来源：000037_wiki_and_indexing.up.sql, 000061_wiki_page_hierarchy.up.sql, 000075_wiki_page_revisions.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 页面ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `slug` | VARCHAR(255) | NOT NULL | URL友好的页面标识，如 entity/acme-corp，知识库内唯一 |
| `title` | VARCHAR(512) | NOT NULL；默认 '' | 页面标题 |
| `page_type` | VARCHAR(32) | NOT NULL；默认 'summary' | 页面类型：summary文档摘要页/entity实体页/concept概念页/index索引页/synthesis综合分析页(Agent按需生成)/comparison对比页(Agent按需生成) |
| `status` | VARCHAR(32) | NOT NULL；默认 'published' | 页面状态：draft草稿/published已发布/archived已归档 |
| `content` | TEXT | NOT NULL；默认 '' | 完整Markdown正文 |
| `summary` | TEXT | NOT NULL；默认 '' | 用于索引列表的一行摘要 |
| `parent_slug` | VARCHAR(255) | NOT NULL；默认 '' | 语义父页面的slug（可为空） |
| `folder_id` | VARCHAR(36) | NOT NULL；默认 '' | 所属Wiki目录树文件夹ID（指向wiki_folders.id，空串为Wiki根目录），是页面位置的唯一事实来源 |
| `category_path` | JSONB | 默认 '[]'::JSONB | 目录面包屑缓存（如[AI,LLM应用,RAG]），由folder_id派生并冗余存储便于列表/排序查询 |
| `wiki_path` | VARCHAR(1024) | NOT NULL；默认 '' | 由页面类型+目录+标题派生的规范化可排序路径 |
| `depth` | INT | NOT NULL；默认 0 | category_path的层级深度缓存 |
| `sort_order` | INT | NOT NULL；默认 0 | 同级页面排序号 |
| `source_refs` | JSONB | 默认 '[]'::JSONB | 该页面引用的来源知识条目（格式"knowledge_id"或"knowledge_id\|标题"），文档级粒度 |
| `chunk_refs` | JSONB | 默认 '[]'::JSONB | 该页面生成时引用的具体来源分块ID列表（证据级粒度，摘要页为空） |
| `in_links` | JSONB | 默认 '[]'::JSONB | 指向本页的反向链接（其他页面slug列表） |
| `out_links` | JSONB | 默认 '[]'::JSONB | 本页链接出去的页面slug列表 |
| `page_metadata` | JSONB | 默认 '{}'::JSONB | 扩展元数据（标签、分类、日期等） |
| `aliases` | JSONB | 默认 '[]'::JSONB | 页面的别名/缩写/译名列表 |
| `version` | INT | NOT NULL；默认 1 | 内容版本号，仅在标题/正文/摘要/类型/状态等用户可见字段变化时递增 |
| `last_edit_source` | VARCHAR(16) | NOT NULL；默认 '' | Author kind of the current version: pipeline \| agent \| user \| revert ( |
| `last_editor_id` | VARCHAR(64) | NOT NULL；默认 '' | User id of the caller that produced the current version (empty for background pipeline writes) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_wiki_pages_kb_slug` (`knowledge_base_id, slug`) [UNIQUE]
- `idx_wiki_pages_kb_id` (`knowledge_base_id`)
- `idx_wiki_pages_page_type` (`knowledge_base_id, page_type`)
- `idx_wiki_pages_parent_slug` (`knowledge_base_id, parent_slug`)
- `idx_wiki_pages_tree` (`knowledge_base_id, page_type, wiki_path, sort_order, title`)
- `idx_wiki_pages_folder` (`knowledge_base_id, folder_id`)
- `idx_wiki_pages_tenant_id` (`tenant_id`)
- `idx_wiki_pages_deleted_at` (`deleted_at`)
- `idx_wiki_pages_fulltext` (`to_tsvector('simple', coalesce(title, ''`)
- `idx_wiki_pages_source_refs` (`source_refs jsonb_path_ops`)
- `idx_wiki_pages_source_refs_text` (`to_tsvector('simple', source_refs::text`)
- `idx_wiki_pages_title_trgm` (`lower(title`)
- `idx_wiki_pages_folder_id` (`folder_id`)
- `idx_wiki_pages_parent_slug` (`knowledge_base_id, parent_slug`)
- `idx_wiki_pages_tree` (`knowledge_base_id, page_type, wiki_path, sort_order, title`)

