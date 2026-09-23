# WeKnora 数据字典

> 事实源：`migrations/versioned/*.up.sql`（107 个迁移脚本按版本序累积为最终状态）+ `internal/types/*.go` 的 GORM 结构体。
> 共 **72 张表**、**972 个字段**。字段名、类型、约束、索引由脚本从迁移脚本机械抽取并经独立口径计数自检，**未经人工改写**；「含义」列在 DDL 无注释时为推断，已逐处标注。

## 表索引

### 租户与组织协作

- [`agent_shares`](agent_shares.md) — 自定义Agent共享到组织（空间）的记录，实现跨租户Agent访问授权
- [`kb_shares`](kb_shares.md) — 知识库共享到组织（空间）的记录，实现跨租户知识库访问授权
- [`organization_join_requests`](organization_join_requests.md) — 组织加入/角色升级申请表，支撑需管理员审批的加入流程
- [`organization_members`](organization_members.md) — 【历史/已废弃】按用户维度的组织成员表，已被按工作空间维度的 organization_tenant_members 取代，代码中不再读写，仅为历史迁移数据保留
- [`organization_tenant_members`](organization_tenant_members.md) — 组织（空间）成员表（按工作空间维度，取代旧的organization_members按用户维度设计），是当前生效的组织成员权限来源
- [`organizations`](organizations.md) — 跨租户协作空间（Organization/Space）：多个工作空间之间共享知识库/Agent的组织单元
- [`tenant_disabled_shared_agents`](tenant_disabled_shared_agents.md) — 记录某工作空间主动“隐藏”某个共享进来的Agent（不在自己对话下拉框显示的个人化设置）
- [`tenant_invitations`](tenant_invitations.md) — 工作空间邀请表：管理员发起的定向邀请或邀请链接，用户接受后生成tenant_members记录
- [`tenant_members`](tenant_members.md) — 工作空间成员表：用户在某工作空间内的角色（RBAC四级角色矩阵）及成员状态
- [`tenants`](tenants.md) — 工作空间（租户）主表：存储空间的检索引擎、Agent/上下文/对话/存储/记忆等全局默认配置，是多租户隔离的根实体
- [`user_kb_pins`](user_kb_pins.md) — 用户维度的知识库置顶记录，替代旧的知识库全局置顶字段，实现按用户个性化的知识库排序
- [`user_resource_favorites`](user_resource_favorites.md) — 用户对知识库/Agent等资源的个人收藏（星标）记录

### 系统运维与基础设施

- [`audit_logs`](audit_logs.md) — 工作空间/平台级操作审计日志：记录RBAC变更、资源增删改、系统管理等关键操作，供安全合规追溯
- [`knowledge_processing_spans`](knowledge_processing_spans.md) — 文档解析处理链路的追踪Span记录，支撑“文档解析追踪时间线”功能与失败排查
- [`resource_access_grants`](resource_access_grants.md) — 资源的临时可撤销访问令牌表，用于生成限时的文件直链访问凭证
- [`resource_bindings`](resource_bindings.md) — 资源与其所有者（知识条目/消息/临时文档等）之间的引用关系表，实现“一份文件多处引用、任一处删除不影响其他”的共享语义
- [`resources`](resources.md) — 文件/对象统一注册表：为每个物理存储对象分配稳定的应用层引用handle，实现跨会话/跨知识库的文件身份与去重
- [`storage_backends`](storage_backends.md) — 工作空间可配置的对象/文件存储后端实例注册表，支持一个工作空间挂载多个存储实例并按知识库绑定
- [`system_settings`](system_settings.md) — 平台级（非工作空间级）运行时可调参数表，供系统管理员在管理界面热更新，无需重启
- [`task_dead_letters`](task_dead_letters.md) — 异步任务失败归档表：重试耗尽后的任务快照，供运维排查与手动补救
- [`task_pending_ops`](task_pending_ops.md) — 通用持久化任务待处理队列（替代原Redis List方案），主要用于Wiki摄取等按批次消费的操作队列

### 用户与认证

- [`auth_tokens`](auth_tokens.md) — 用户身份令牌表：JWT等access/refresh token的持久化与吊销状态
- [`tenant_api_keys`](tenant_api_keys.md) — 工作空间/平台级API Key表：面向程序化集成的可撤销机器凭证，支持按能力(capability)与知识库范围限权
- [`users`](users.md) — 用户账号表：登录凭证、所属默认租户及个人偏好设置

### 智能体、技能与沙箱

- [`browser_devices`](browser_devices.md) — 浏览器扩展远程控制配对成功后的长期设备凭证表：每个租户/用户当前仅保留一个已注册设备，供Agent通过Chrome插件操作用户本地浏览器
- [`browser_pairings`](browser_pairings.md) — 浏览器扩展一次性配对令牌表：用户首次授权浏览器插件时的短时配对凭证，兑换成功后即删除
- [`browser_task_interruptions`](browser_task_interruptions.md) — 标记因浏览器连接中断而需要显式恢复的会话，供重新连接后续跑被打断的浏览器操作任务
- [`custom_agents`](custom_agents.md) — 自定义/内置智能体（Agent）定义：问答模式、系统提示词、工具/知识库范围、检索策略等全套运行配置
- [`fork_snapshot_leases`](fork_snapshot_leases.md) — 会话Fork（分支）功能中，创建分支会话行之前先落库的沙箱快照租约，防止创建过程崩溃导致快照孤儿无法回收
- [`tenant_sandbox_configs`](tenant_sandbox_configs.md) — 工作空间的技能沙箱后端配置：定义Agent执行脚本所用的Docker/E2B/Cube等沙箱环境连接信息
- [`tenant_skill_catalog`](tenant_skill_catalog.md) — 工作空间技能目录（定义级）：一份技能定义可被安装到多个沙箱配置，压缩包仅在此表持有一份
- [`tenant_skill_snapshots`](tenant_skill_snapshots.md) — 沙箱镜像链路的快照台账：记录每次安装/卸载/重建产生的Provider侧快照及其父子链，防止快照资源泄漏或失联
- [`tenant_skills`](tenant_skills.md) — 安装到某个沙箱配置镜像中的技能（Skill）实例：记录安装状态、说明文档、环境变量声明及镜像服务版本
- [`tenant_user_env_vars`](tenant_user_env_vars.md) — 按调用主体（用户/IM用户等）维度的个人环境变量表：为沙箱执行/特定技能提供个人化的密钥等变量值

### 分块与向量检索

- [`chunk_revisions`](chunk_revisions.md) — 分块内容被覆盖前的历史版本快照，支撑分块编辑的“版本历史+回滚”功能
- [`chunks`](chunks.md) — 知识切分后的最小检索单元（文本块），是向量/关键词检索的直接对象，支持编辑与版本回溯
- [`embeddings`](embeddings.md) — 向量检索的旧版一体化存储表（PostgreSQL内置pgvector方案）：文本内容+向量+来源引用
- [`vector_stores`](vector_stores.md) — 租户可配置的向量数据库实例注册表：支持ES/Qdrant/Milvus/Weaviate/腾讯VectorDB/Doris/OpenSearch等多引擎多实例

### 数据源与外部同步

- [`data_sources`](data_sources.md) — 外部数据源连接配置：飞书/Notion/GitLab/语雀/钉钉文档/RSS等自动同步知识的数据源定义
- [`sync_logs`](sync_logs.md) — 数据源每次同步任务的执行记录：处理条目统计与错误明细

### MCP与渠道集成

- [`embed_channels`](embed_channels.md) — 网站嵌入式对话组件（Widget）发布配置：把某个Agent以可嵌入外部网站的聊天窗口形式对外发布
- [`im_channel_sessions`](im_channel_sessions.md) — IM平台用户/群聊与WeKnora会话的映射表，实现企业微信/飞书等IM渠道消息与内部会话的绑定
- [`im_channels`](im_channels.md) — IM渠道（企业微信/飞书等）接入配置：每个渠道绑定一个Agent对外提供问答服务
- [`mcp_endpoints`](mcp_endpoints.md) — 工作空间对外发布的MCP Server端点：允许Claude Desktop/Cursor等外部MCP客户端通过Streamable HTTP连接并调用受限工具集
- [`mcp_metadata`](mcp_metadata.md) — MCP服务的工具/资源目录快照缓存：按(服务,调用主体)显式同步的完整工具列表，供Agent发现工具而无需每次实时连接MCP服务器
- [`mcp_oauth_clients`](mcp_oauth_clients.md) — MCP服务的OAuth动态注册客户端凭证缓存，每个(租户,服务)注册一次并复用，避免重复注册
- [`mcp_oauth_tokens`](mcp_oauth_tokens.md) — MCP服务按调用主体（用户/IM用户/嵌入访客等）维度存储的OAuth访问/刷新令牌
- [`mcp_services`](mcp_services.md) — 租户配置的MCP（Model Context Protocol）外部工具服务连接定义
- [`mcp_tool_approvals`](mcp_tool_approvals.md) — MCP服务下各工具的启用/人工审批策略覆盖表，实现高风险工具调用前的人工确认
- [`web_search_providers`](web_search_providers.md) — 租户配置的联网搜索服务商实例（Bing/Google/Tavily/Bocha等），供Agent联网检索使用

### 知识库与知识管理

- [`knowledge_bases`](knowledge_bases.md) — 知识库主表：一个知识库对应一套分块/向量化/存储/FAQ/Wiki等配置，是知识组织的顶层容器
- [`knowledge_tag_relations`](knowledge_tag_relations.md) — 知识条目与标签的多对多关联表
- [`knowledge_tags`](knowledge_tags.md) — 知识库内的标签（分类）定义，用于给文档/FAQ分块打标签分类
- [`knowledges`](knowledges.md) — 知识条目（文档/URL/FAQ导入/手写Markdown等）主表：记录文件元信息、解析状态与生成的摘要/画像

### 长期记忆

- [`memory_doc_affinity`](memory_doc_affinity.md) — 记录某用户的回答反复引用某份文档的次数，是唯一无需用户主动提供的“个人检索偏好”信号，用于个性化召回排序
- [`memory_extraction_sessions`](memory_extraction_sessions.md) — 长期记忆后台抽取任务按会话维度的进度台账：记录每个会话抽取到的消息游标及失败重试信息，替代旧版全局游标
- [`memory_item_embeddings`](memory_item_embeddings.md) — 长期记忆条目的向量表示，独立建表避免高频列表查询携带向量数据，仅语义召回时读取
- [`memory_items`](memory_items.md) — 单条长期记忆陈述：从对话中抽取或用户显式要求记住的关于该用户的事实/偏好/画像/任务/兴趣
- [`memory_subjects`](memory_subjects.md) — 长期记忆的“记忆空间”主体：一个工作空间内一个调用主体（用户/IM用户/访客等）对应一个记忆空间，存有渲染好的常驻记忆文本块
- [`memory_tombstones`](memory_tombstones.md) — 用户主动要求“忘记”的记忆的墓碑记录：仅保存指纹哈希不保存原文，防止后台抽取任务从同一条消息再次生成相同记忆
- [`memory_topic_stats`](memory_topic_stats.md) — 记忆主题命中次数统计表：某用户反复被问到/提到的主题达到阈值后才升级为“长期关注点(interest)”记忆

### 会话与消息

- [`message_artifacts`](message_artifacts.md) — 助手消息在沙箱中执行技能脚本产生并持久化的文件产物明细（如生成的Word/PPT/图表文件）
- [`message_suggestion_events`](message_suggestion_events.md) — 推荐问题的曝光/点击/关闭/重新生成等产品分析埋点事件表，与安全审计日志分离
- [`message_suggestion_sets`](message_suggestion_sets.md) — 每条助手消息的追问/推荐问题生成结果的持久化缓存记录（含生成过程用量统计）
- [`messages`](messages.md) — 会话中的单条消息（用户提问或助手回答），承载检索引用、Agent执行步骤、附件产物与用量统计
- [`sessions`](sessions.md) — 对话会话主表：一次用户与Agent的多轮对话上下文及其检索/召回策略参数
- [`temporary_documents`](temporary_documents.md) — 会话级临时附件文档：用户在对话中上传的、有效期有限的文件及其解析产物，独立于正式知识库

### 模型管理

- [`models`](models.md) — 租户下配置的 AI 模型清单：Embedding/Rerank/对话(KnowledgeQA)/多模态(VLLM)/语音识别(ASR) 等各类模型的连接参数

### Wiki知识图谱

- [`wiki_folders`](wiki_folders.md) — Wiki浏览器的目录树节点，支持独立于页面存在的空文件夹用于组织页面
- [`wiki_page_issues`](wiki_page_issues.md) — Wiki页面质量问题上报表（如内容矛盾、链接失效等），供人工/Agent审阅修复
- [`wiki_page_revisions`](wiki_page_revisions.md) — Wiki页面被覆盖前的历史版本快照，支撑“版本历史+行级Diff+一键回滚”功能
- [`wiki_pages`](wiki_pages.md) — Wiki模式下由Agent从原始文档蒸馏生成的互链Markdown知识页面，是自维护知识库/知识图谱的核心实体

## 关键业务关系

下列关系分两类：**显式外键**（DDL 里有 `REFERENCES` 约束，DB 层强制）与**逻辑关联**（仅靠应用层 + 索引维护，DDL 无约束）。后者已逐条标注。

### 知识与内容
- `knowledges.knowledge_base_id` → `knowledge_bases.id`（文档归属知识库；索引 `idx_knowledges_base_id`）
- `chunks.knowledge_id` → `knowledges.id`、`chunks.knowledge_base_id` → `knowledge_bases.id`（分块归属）
- `knowledge_tag_relations.knowledge_id` → `knowledges.id`、`.tag_id` → `knowledge_tags.id`（多对多标签，联合主键）
- `chunk_revisions.chunk_id` → `chunks.id`（分块历史版本；唯一索引 `chunk_id+revision`）
- `knowledge_bases.vector_store_id` → `vector_stores.id`（代码注释明确为逻辑引用，NULL 表示走租户默认向量库）

### 会话与消息
- `messages.session_id` → `sessions.id`（索引 `idx_messages_session_id`）
- `message_artifacts.message_id` → `messages.id`（唯一索引 `message_id+position`）
- `message_suggestion_sets.assistant_message_id` → `messages.id`
- `message_suggestion_events.suggestion_set_id` → `message_suggestion_sets.id`（**显式外键 ON DELETE CASCADE**）
- `sessions.parent_session_id` → `sessions.id`（会话 Fork 自引用；代码注释明确「故意不设外键，父会话删除不应级联删除分支」）
- `sessions.agent_id` → `custom_agents.id` **（待确认：与 custom_agents 复合主键 (id, tenant_id) 之间未见显式外键，为逻辑关联）**

### 租户、组织与共享
- `custom_agents` 复合主键 `(id, tenant_id)`；`agent_shares (agent_id, source_tenant_id)` → `custom_agents (id, tenant_id)`（**显式复合外键**）
- `kb_shares.knowledge_base_id` → `knowledge_bases.id`、`.organization_id` → `organizations.id`（**均为显式外键 ON DELETE CASCADE**）
- `agent_shares.organization_id`、`organization_tenant_members.organization_id`、`organization_join_requests.organization_id` → `organizations.id`（**均为显式外键 ON DELETE CASCADE**）
- `users.tenant_id` → `tenants.id`（**显式外键 `fk_users_tenant` ON DELETE SET NULL**）
- `auth_tokens.user_id` → `users.id`（**显式外键 `fk_auth_tokens_user` ON DELETE CASCADE**）
- `tenant_members (user_id, tenant_id)`（唯一索引）**（待确认：未见显式外键，逻辑关联）**
- `tenant_api_keys.tenant_id` → `tenants.id`（**显式外键 ON DELETE CASCADE**；已放宽为可空以支持平台级 Key，见 `chk_tenant_api_keys_scope` 约束）
- `organizations.owner_id` → `users.id`、`.owner_tenant_id` → `tenants.id` **（待确认：Go 侧仅以 `gorm:"foreignKey:OwnerID"` 声明关联，DDL 未见外键约束）**

### MCP、渠道与数据源
- `mcp_tool_approvals.service_id`、`mcp_oauth_clients.service_id`、`mcp_oauth_tokens.service_id`、`mcp_metadata.service_id` → `mcp_services.id`（**均为显式外键 ON DELETE CASCADE**）
- `im_channel_sessions.session_id` → `sessions.id`（**显式外键 ON DELETE CASCADE**）；`.im_channel_id` → `im_channels.id` **（待确认：有索引无外键）**
- `sync_logs.data_source_id` → `data_sources.id`（**显式外键 ON DELETE CASCADE**）
- `data_sources.knowledge_base_id` → `knowledge_bases.id` **（待确认：有索引 `idx_data_sources_knowledge_base_id`，无外键）**
- `mcp_endpoints.knowledge_base_ids` 为 JSON 数组，逻辑指向多个 `knowledge_bases.id`，由应用层校验

### 资源与存储
- `resource_bindings.resource_id`、`resource_access_grants.resource_id` → `resources.id`（**均为显式外键 ON DELETE CASCADE**）
- `resources.storage_backend_id`、`knowledge_bases.storage_backend_id`、`tenants.default_storage_backend_id` → `storage_backends.id` **（待确认：均为逻辑引用，未见外键约束）**
- `temporary_documents.session_id` → `sessions.id` **（待确认：有索引 `idx_temporary_documents_scope`，无外键）**

### Wiki
- `wiki_pages.knowledge_base_id` → `knowledge_bases.id`；`.folder_id` → `wiki_folders.id`（代码明确 `folder_id` 是页面位置的唯一事实来源，`category_path` 为其派生冗余）
- `wiki_page_revisions.page_id` → `wiki_pages.id`（唯一索引 `page_id+version`）
- `wiki_folders.parent_id` → `wiki_folders.id`（自引用邻接表，构成目录树）

### 长期记忆
- `memory_items`、`memory_topic_stats`、`memory_doc_affinity`、`memory_tombstones`、`memory_extraction_sessions` 的 `subject_id` → `memory_subjects.subject_id`（按 `(tenant_id, subject_id)` 逻辑关联；`subject_id` 是字符串主体标识而非自增 ID）
- `memory_item_embeddings.item_id` → `memory_items.id`（一对一，主键即外键语义）**（待确认：未见显式外键约束）**

### 智能体、技能与沙箱
- `tenant_skills.catalog_id` → `tenant_skill_catalog.id`（代码注释明确为逻辑关联）
- `tenant_skill_snapshots.skill_id` → `tenant_skills.id`、`.sandbox_config_id` → `tenant_sandbox_configs.id` **（待确认：均为逻辑引用）**
- `tenant_user_env_vars.sandbox_config_id` → `tenant_sandbox_configs.id`、`.skill_id` → `tenant_skills.id`（逻辑关联，唯一索引覆盖）
- `sessions.sandbox_config_id` → `tenant_sandbox_configs.id`（逻辑引用；特殊哨兵值 `"-"` 表示历史遗留的「部署级默认配置」）
- `custom_agents.config` 内嵌 JSON 字段（`sandbox_config_id`、`knowledge_bases`、`mcp_services`、`web_search_provider_id`、`model_id`）分别软引用对应表，均由应用层校验

## 待确认清单

- [ ] `organization_members` 表在当前代码中已无任何读写引用，推断已被 `organization_tenant_members` 完全取代（见 `organization.go` 注释「Plan 3 (#1303) lifts the abstraction from per-user to per-tenant」）——是否可计划下线
- [ ] `knowledge_bases.is_pinned` / `pinned_at` 代码标注为遗留字段（`gorm:"-"`，不再读写，已由 `user_kb_pins` 按用户维度取代）——是否可在未来迁移中物理清理
- [ ] `mcp_oauth_tokens.user_id` 与新增的 `principal_type`/`principal_id` 是否并行冗余，`user_id` 是否已可下线
- [ ] `knowledge_bases.cos_config`（列名仍为 cos_config）与新版 `storage_provider_config` 的迁移完成度、遗留数据规模，代码中未量化
- [ ] 多处 `tenant_id` / `knowledge_base_id` 等关系在 DB 层未建实际外键（仅靠应用层 + 索引维护一致性），上文已逐条标注——请确认这是有意的设计取舍（性能 / 跨库兼容）还是待补齐
