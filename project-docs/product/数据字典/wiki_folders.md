## 表：wiki_folders

> 业务含义：Wiki浏览器的目录树节点，支持独立于页面存在的空文件夹用于组织页面
> 来源：000037_wiki_and_indexing.up.sql, 000061_wiki_page_hierarchy.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | 文件夹ID |
| `tenant_id` | BIGINT | NOT NULL；默认 0 | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `parent_id` | VARCHAR(36) | NOT NULL；默认 '' | 父文件夹ID，空串表示根目录 |
| `name` | VARCHAR(255) | NOT NULL | 文件夹名称 |
| `path` | VARCHAR(1024) | NOT NULL；默认 '' | 由名称链拼接而成的展示用完整路径 |
| `depth` | INT | NOT NULL；默认 0 | 目录层级深度 |
| `sort_order` | INT | NOT NULL；默认 0 | 同级排序号 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL；默认 NOW() | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_wiki_folders_parent_name` (`knowledge_base_id, parent_id, name`) [UNIQUE]
- `idx_wiki_folders_parent` (`knowledge_base_id, parent_id`)
- `idx_wiki_folders_deleted_at` (`deleted_at`)
- `idx_wiki_folders_parent_name` (`knowledge_base_id, parent_id, name`) [UNIQUE]
- `idx_wiki_folders_parent` (`knowledge_base_id, parent_id`)
- `idx_wiki_folders_deleted_at` (`deleted_at`)

