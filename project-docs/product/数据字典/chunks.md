## 表：chunks

> 业务含义：知识切分后的最小检索单元（文本块），是向量/关键词检索的直接对象，支持编辑与版本回溯
> 来源：000000_init.up.sql, 000001_agent.up.sql, 000003_chunk_flags.up.sql, 000010_add_seq_id.up.sql, 000033_add_video_info_to_chunks.up.sql, 000078_chunk_editing_and_custom_metadata.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | 分块ID |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID |
| `knowledge_base_id` | VARCHAR(36) | NOT NULL | 所属知识库ID |
| `knowledge_id` | VARCHAR(36) | NOT NULL | 所属知识条目ID |
| `content` | TEXT | NOT NULL | 分块当前文本内容（可被用户编辑） |
| `chunk_index` | INTEGER | NOT NULL | 在原文档中的顺序位置 |
| `is_enabled` | BOOLEAN | NOT NULL；默认 true | 是否启用参与检索 |
| `start_at` | INTEGER | NOT NULL | 在原文中的起始字符位置 |
| `end_at` | INTEGER | NOT NULL | 在原文中的结束字符位置 |
| `pre_chunk_id` | VARCHAR(36) | — | 前一个分块ID |
| `next_chunk_id` | VARCHAR(36) | — | 后一个分块ID |
| `chunk_type` | VARCHAR(20) | NOT NULL；默认 'text' | 分块类型：text普通文本/parent_text父子分块的父块(不参与向量索引)/image_ocr图片OCR/image_caption图片描述/summary摘要/entity实体/relationship关系/faq问答对/web_search联网搜索结果/table_summary表格摘要/table_column表格列描述/wiki_page Wiki页面同步块 |
| `parent_chunk_id` | VARCHAR(36) | — | 父分块ID（用于图片块/关系块关联原文本块，或父子分块策略中的父块） |
| `image_info` | TEXT | — | 图片相关信息（URL、OCR文本、图片描述等，JSON文本） |
| `relation_chunks` | JSONB | — | 关联的关系类型分块ID列表 |
| `indirect_relation_chunks` | JSONB | — | 间接关联的关系分块ID列表 |
| `metadata` | JSONB | — | 分块级扩展元数据（如FAQ元数据） |
| `tag_id` | VARCHAR(36) | — | 所属标签ID（主要用于FAQ按标签分类） |
| `status` | INT | NOT NULL；默认 0 | 分块状态：0默认/1已存储/2已索引 |
| `content_hash` | VARCHAR(64) | — | 内容哈希，用于快速匹配（主要用于FAQ去重） |
| `flags` | INTEGER | NOT NULL；默认 1 | 位标志字段（如是否可被推荐，默认可推荐） |
| `seq_id` | BIGINT | NOT NULL；默认 nextval('chunks_seq_id_seq')*/；后续变更：SET DEFAULT nextval('chunks_seq_id_seq') | 自增序列ID，供外部API（如FAQ条目）按序引用 |
| `video_info` | TEXT | — | Video information in JSON format: {"url": string, "frame_count": int, "has_vlm_analysis": bool, "has_asr": bool, "video_summary": string, "asr_text": string, "frame_descriptions": string[]} |
| `source_content` | TEXT | NOT NULL；默认 '' | 解析器原始输出内容（不可变），首次人工编辑时从content惰性回填 |
| `content_revision` | INT | NOT NULL；默认 0 | 内容修订版本号，每次人工编辑或回滚时递增 |
| `index_status` | VARCHAR(16) | NOT NULL；默认 'ready' | 内容是否已同步到检索索引：ready已就绪/processing索引中/failed索引失败 |
| `last_editor_id` | VARCHAR(64) | NOT NULL；默认 '' | 产生当前版本内容的操作者标识 |
| `context_header` | TEXT | NOT NULL；默认 '' | 索引时前置拼接的Markdown标题面包屑，持久化以便后续编辑重建相同索引输入 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_chunks_tenant_kg` (`tenant_id, knowledge_id`)
- `idx_chunks_parent_id` (`parent_chunk_id`)
- `idx_chunks_chunk_type` (`chunk_type`)
- `idx_chunks_tag` (`tag_id`)
- `idx_chunks_content_hash` (`content_hash`)
- `idx_chunks_seq_id` (`seq_id`) [UNIQUE]
- `idx_chunks_kb_tenant` (`knowledge_base_id, tenant_id`)
- `idx_chunks_knowledge_enabled` (`knowledge_id, is_enabled, deleted_at`)

