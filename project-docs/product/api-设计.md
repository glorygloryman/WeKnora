# WeKnora API 设计

> 事实源：`docs/swagger.json`（374 个 operation，371 个带 summary）+ `internal/router/*.go` 路由注册（463 个端点）+ `internal/handler/*.go` 的 swaggo 注解块。
> 接口说明与参数说明**取注解原文**，未作改写或润色；注解未覆盖的端点已单独标注「无接口注解，用途由代码反推」。
> 鉴权列来自 `internal/router/rbac.go` 守卫与 API Key 能力位，完整权限模型见[权限矩阵](权限矩阵.md)。

## 全局约定

**basePath**：`/api/v1`（`docs/swagger.json` 的 `basePath` 字段）。本文档全部端点均给出补全后的完整路径。只有 4 条路由完全不挂在 `/api/v1` 下：`GET /health`、`GET /swagger/*any`（仅 `GIN_MODE != release` 时注册）、`GET /files`、`GET+HEAD /r/:token`。

**统一响应形态**：
- 成功：`c.JSON(http.StatusOK, gin.H{"success": true, "data": <...>})`，`data` 的实际类型见各端点"出参"。文件流/下载/预览类端点（导出 FAQ、下载知识文件、批量下载 ZIP、presigned 系列）直接返回二进制流或 302 重定向，不走该包装。
- 失败：统一由 `internal/middleware/error_handler.go` 的 `ErrorHandler()` 中间件在 `c.Error(err)` 后拦截：若是 `*errors.AppError`，返回 `{"success": false, "error": {"code": <int>, "message": <string>, "details": <any，可省略>}}`，HTTP 状态码取 `AppError.HTTPCode`；否则统一 500 + `{"success": false, "error": {"code": 1007, "message": "Internal server error"}}`。
- 例外：`System Admin` 模块下的 `/system/admin/settings*`、`/system/admin/runtime/*` 按代码注释明确"不走 `data` 包装，直接返回裸行/数组，以匹配前端 axios 拦截器约定（`frontend/src/utils/request.ts:97`）"。
- swagger 里绝大多数 `@Success 200 {object} map[string]interface{}` 实际只描述 `data` 内部形状（多为未强类型的 `object`），下文"出参"字段延续这一层，不代表整个 HTTP body。

**公共鉴权头**：
- `Authorization: Bearer <JWT>`（登录态）与 `X-API-Key: <token>`（空间/平台 API Key）二选一；`securityDefinitions.ApiKeyAuth` 说明"平台 Key 调用空间接口时需同时传 `X-Tenant-ID`"。
- `internal/middleware/auth.go` 的 `Auth()` 中间件顺序：先试 Bearer（无效不立即拒绝）→ 再试 `X-API-Key` → 都没有才 401；这样"携带过期 JWT 但同时带有效 API Key"的客户端仍可通过。
- **完全公开、绕过 Auth 中间件**（`noAuthAPI` 白名单 + 两处注册在中间件挂载之前/根路由的例外）：`GET /health`、`POST /auth/register`、`POST /auth/login`、`POST /auth/auto-setup`、`POST /auth/invitations/lookup`、`POST /auth/register-by-invite`、`GET /auth/config`、`GET /auth/oidc/{config,url,start,callback}`、`POST /auth/refresh`、`GET+HEAD /files/presigned`、`GET /mcp-oauth/callback`（state 参数自校验）、`GET/POST /im/callback/:channel_id`（IM 平台签名自校验）、`GET+HEAD /r/:token`（能力令牌自校验）、`GET /api/v1/local-browser/*`（注册在 Auth 中间件挂载之前）、`GET /swagger/*any`。
- **需认证但租户可选**（`isTenantOptionalAPI`，未选定租户也放行）：`GET/PUT /auth/me`、`PUT /auth/me/preferences`、`POST /auth/logout`、`POST /auth/change-password`、`GET /auth/validate`、`POST /auth/switch-tenant`、`POST /tenants`、`GET+POST /me/invitations*`；其余需认证路由若解析不出租户会报 `TENANT_REQUIRED`。
- **API Key 能力位**（`types.APIKeyCapability`，`internal/types/tenant_api_key.go`）：`retrieve chat read_agents ingest manage_kbs manage_agents message_history manage_models manage_mcp_services manage_datasources manage_channels manage_vector_stores manage_storage_backends manage_web_search run_evaluations manage_members manage_spaces manage_tenant_settings`，以及平台级 `system_tenants_read/manage system_settings_read/manage system_runtime_read/manage system_audit_read`。带 `full_access` 标记的 Key 绕过所有细分能力检查；否则必须显式拥有该路由登记的能力之一。路由层用 `apiKeyGroup`/`apiKeyRoute` 显式登记每条 Key 可达路由，**未登记路由对任何 API Key 一律 fail-closed 拒绝**，JWT 会话不受此闸门影响（这是与角色 Guard 完全正交的第二套门禁，下文"鉴权"字段分别给出两者）。

**必填口径**：表格"必填"列取自 swagger `required` 字段，是**参数绑定层**必填（对应 Go struct `binding:"required"` 或路径参数天然必填），不等于业务必填——例如很多 `PUT` 的 `request body` 整体必填，但内部字段基本都是"未提供则保持不变"的可选补丁语义；具体到字段级需查看对应 DTO（`internal/handler/dto/*.go` 或 handler 内联 struct）。

**分页参数**（两套并存，按端点选用其一）：
1. 页码分页 `parseListPagination`（`internal/handler/list_pagination.go`）：`page`（默认 1）+ `page_size`（默认 20，上限 100，越界返回 400 `ErrValidation`）。
2. 偏移分页 `parseOffsetPagination`（同文件）：`offset`（默认 0）+ `limit`（默认 20，上限 100）。
3. 少数端点用游标分页（审计日志 `after_id`+`limit`；Wiki 索引/版本 `cursor`/`offset`+`limit`），语义各自独立，见对应端点参数表。

---

## 端点总览

| 模块 | 端点数（swagger） | 做什么 |
|---|---|---|
| [知识管理](#知识管理) | 23 | 知识条目（文档）的增删改查、批量重解析/删除/移动、摘要生成、图片信息更新、下载预览 |
| [组织管理](#组织管理) | 23 | 跨租户组织的创建/搜索/加入/成员与角色管理、知识库与智能体的组内共享 |
| [Wiki](#wiki) | 21 | 知识库内 Wiki 页面/文件夹的编写、版本、索引、知识图谱、Lint 质量检查与问题跟踪 |
| [MCP服务](#mcp服务) | 20 | 外部 MCP 工具服务的接入、凭证、OAuth 授权、工具/资源目录、工具调用审批 |
| [认证](#认证) | 17 | 注册、登录、OIDC、令牌刷新校验、密码修改、空间切换 |
| [初始化](#初始化) | 17 | 知识库模型/存储引擎初始化配置，及 Ollama/远程模型/Embedding/Rerank/ASR/抽取自检 |
| [SandboxConfig](#sandboxconfig) | 17 | 智能体沙箱环境模板配置及内置 Skill 的安装/管理 |
| [长期记忆](#长期记忆) | 16 | 用户长期记忆条目、主题、来源文档的查看、确认/拒绝、导出与整理 |
| [DataSource](#datasource) | 15 | 外部数据源连接器的接入、凭证、资源浏览、同步任务调度与日志 |
| [会话](#会话) | 15 | 聊天会话的创建/列表/更新/删除、临时附件、消息转向(steer)、产物、沙箱终端/桌面 |
| [System Admin](#system-admin) | 15 | 平台级系统管理员操作：提升/撤销系统管理员、系统设置、运行时队列、平台审计 |
| [空间管理](#空间管理) | 14 | 空间（租户）创建、查询、KV 配置项、API Key 管理 |
| [FAQ管理](#faq管理) | 13 | 知识库内 FAQ 条目的增删改查、批量导入、相似问维护、搜索 |
| [知识库](#知识库) | 13 | 知识库的创建/更新/删除/复制、混合检索、Pin、迁移目标查询 |
| [问答](#问答) | 9 | 知识问答、智能体问答、知识检索接口（SSE 流式返回） |
| [智能体](#智能体) | 9 | 自定义智能体（Agent）的增删改查、复制、占位符与类型预设 |
| [StorageBackend](#storagebackend) | 9 | 对象存储后端实例的注册、测试、设为默认 |
| [系统](#系统) | 8 | 系统信息、部署能力清单、解析引擎/存储引擎自检、沙箱连通性测试 |
| [VectorStore](#vectorstore) | 8 | 向量库实例的注册与连接测试 |
| [MCP端点](#mcp端点) | 7 | 面向外部客户端暴露的 MCP Endpoint（工具目录、令牌轮换） |
| [Skills](#skills) | 7 | Skill 目录的注册/安装/文件查看/卸载 |
| [网络搜索](#网络搜索) | 7 | 网络搜索 Provider 的类型、配置、测试 |
| [分块管理](#分块管理) | 6 | 文档分块（chunk）的查询、更新、删除、版本回退、生成问题维护 |
| [模型管理](#模型管理) | 6 | 模型 Provider 的注册、调试、更新、删除、凭证管理 |
| [IM 渠道](#im-渠道) | 5 | IM（企业微信/飞书/钉钉等）渠道的更新、删除、启停 |
| [知识库共享](#知识库共享) | 5 | 知识库分享给组织/成员、分享权限管理 |
| [Me](#me) | 5 | 当前用户的 local-browser 浏览器扩展连接账号信息 |
| [我的邀请](#我的邀请) | 5 | 当前用户收到的空间邀请收件箱：查看、接受、拒绝 |
| [空间成员](#空间成员) | 5 | 空间成员的邀请、角色变更、移除、离开 |
| [标签管理](#标签管理) | 4 | 知识库标签的增删改查 |
| [消息](#消息) | 4 | 会话消息的搜索、加载、删除、聊天历史统计 |
| [空间邀请](#空间邀请) | 4 | 空间邀请的发出、列出、撤销、生成共享邀请链接 |
| [组织](#组织) | 3 | 智能体跨组织共享的查看与取消（与「组织管理」重叠，见待确认） |
| [未分类](#未分类) | 3 | 未打 swaggo `@Tags` 的端点（消息产物列表/下载相关） |
| [User](#user) | 3 | 当前用户收藏资源（Star/Unstar）的增删查 |
| [评估](#评估) | 2 | 知识库问答效果评估任务的执行与结果查询 |
| [IM 回调](#im-回调) | 2 | IM 平台消息回调 Webhook（GET/POST 两种校验方式） |
| [知识](#知识) | 2 | 知识移动到其他知识库及进度查询（与「知识管理」重叠，见待确认） |
| [WeKnoraCloud](#weknoracloud) | 2 | WeKnoraCloud 托管模型凭证保存与状态检查 |
| [审计日志](#审计日志) | 2 | 空间级/平台级操作审计日志查询 |
| [分块](#分块) | 1 | 分块结果预览（与「分块管理」重叠，见待确认） |
| [Knowledge](#knowledge) | 1 | 知识搜索（与「知识管理」重叠，英文 tag，见待确认） |
| [系统管理](#系统管理) | 1 | 解析任务队列运行时状态（与「System Admin」重叠，见待确认） |

共 43 个模块 / 374 条 swagger 端点记录，对应 371 个不同的已文档化真实端点；另有 92 个已实现但未打 swaggo 注解的端点，按功能归入下方各模块小节末尾清单（一条不漏，逐条列在其所属模块最后）。

---

## 各模块端点明细

### 知识管理

#### GET /api/v1/knowledge/:id/spans

> ⚠ 本条的 swagger 注解把 basePath 写重了（`@Router /api/v1/knowledge/{id}/spans` 叠加 basePath 后变成 `/api/v1/api/v1/...`）。**上面是真实可调用路径**；注解缺陷见「注解与实现的差异」A1。

**获取知识文档解析的 Span 树（含历史尝试）**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |
| attempt | 指定尝试号；省略=最新 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：⚠️ 该路径在路由树中不存在（`@Router` 把 basePath 写重了），见「注解与实现的差异」。真实路由 `GET /api/v1/knowledge/:id/spans` 的鉴权是 Viewer + KBAccessReadFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/knowledge-bases/:id/knowledge

**清空知识库内容**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（清空任务已提交）
- **鉴权**：Admin + KBAccessWrite(id)（`.With(apiKeyFullAccess())` 覆盖组默认能力位）；API Key：apiKeyFullAccess（覆盖为仅 full-access）

#### GET /api/v1/knowledge-bases/:id/knowledge

**获取知识列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| page | 页码 | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |
| tag_ids | 标签ID筛选，逗号分隔（OR语义） | query | string | 否 |
| keyword | 关键词搜索 | query | string | 否 |
| file_type | 文件类型筛选 | query | string | 否 |
| parse_status | 解析状态筛选 (pending/processing/completed/failed) | query | string | 否 |
| source | 来源/渠道筛选 (web/api/feishu/notion/yuque/wechat/...，或 manual/url 按 type 过滤) | query | string | 否 |
| start_time | 更新时间起点，RFC3339 格式 | query | string | 否 |
| end_time | 更新时间终点，RFC3339 格式 | query | string | 否 |
| folder_path | 文件夹路径筛选，空字符串表示知识库根目录；不传该参数则不按文件夹过滤 | query | string | 否 |
| folder_recursive | 为 true 时同时返回子文件夹内的文档 | query | boolean | 否 |

- **出参**：object（未强类型，字段见 summary/description）（知识列表）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/knowledge/batch-download

**批量下载知识文件**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 文档ID列表 | body | BatchDownloadKnowledgeRequest | 是 |

- **出参**：file（ZIP 压缩包）
- **鉴权**：Contributor + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/knowledge/file

**从文件创建知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| file | 上传的文件 | formData | file | 是 |
| fileName | 自定义文件名 | formData | string | 否 |
| metadata | 元数据JSON | formData | string | 否 |
| enable_multimodel | 启用多模态处理 | formData | boolean | 否 |
| tag_ids | 分类ID列表，逗号分隔 | formData | string | 否 |
| process_config | 处理配置JSON（KnowledgeProcessOverrides） | formData | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（创建的知识）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/knowledge/folders

**获取知识库文件夹目录树**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（目录树）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id/knowledge/folders

**重命名或移动文件夹**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 重命名请求 | body | RenameKnowledgeFolderRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（重命名成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/knowledge/manual

**手工创建知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 手工知识内容 | body | ManualKnowledgePayload | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的知识）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/knowledge/url

**从URL创建知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | URL请求 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的知识）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge/batch

**批量获取知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| ids | 知识ID列表 | query | string[] | 是 |
| kb_id | 可选，知识库ID（用于共享知识库时指定范围） | query | string | 否 |
| agent_id | 可选，共享智能体ID（用于按智能体空间批量拉取文件详情） | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（知识列表）
- **鉴权**：Viewer；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge/batch-delete

**批量删除知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 批量删除请求 | body | BatchDeleteKnowledgeRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Contributor（批量操作跨多个 KB，不做单 KB KBAccess 校验）；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge/batch-reparse

**批量重新解析知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 批量重解析请求 | body | batchReparseKnowledgeRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（任务已提交）
- **鉴权**：Contributor（批量操作跨多个 KB，不做单 KB KBAccess 校验）；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge/folder

**移动知识到文件夹**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 移动请求 | body | MoveKnowledgeToFolderRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（移动成功）
- **鉴权**：Contributor（批量操作跨多个 KB，不做单 KB KBAccess 校验）；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge/image/:id/:chunk_id

**更新图像信息**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |
| chunk_id | 分块ID | path | string | 是 |
| request | 图像信息 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge/manual/:id

**更新手工知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |
| request | 手工知识内容 | body | ManualKnowledgePayload | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的知识）
- **鉴权**：OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge/tags

**批量更新知识标签**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 标签更新请求（updates 必填，kb_id 可选） | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：Contributor（批量操作跨多个 KB，不做单 KB KBAccess 校验）；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/knowledge/:id

**删除知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（任务已提交，返回 task_id）
- **鉴权**：OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge/:id

**获取知识详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（知识详情）
- **鉴权**：Viewer + KBAccessReadFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge/:id

**更新知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |
| request | 更新字段（均可选） | body | UpdateKnowledgeRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge/:id/cancel-parse

**取消知识解析**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（取消已提交）
- **鉴权**：OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge/:id/download

**下载知识文件**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |

- **出参**：file（文件内容）
- **鉴权**：Contributor + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge/:id/preview

**预览知识文件**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |

- **出参**：file（文件内容）
- **鉴权**：Viewer + KBAccessReadFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge/:id/reparse

**重新解析知识**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识ID | path | string | 是 |
| body | 可选的处理配置覆盖 | body | object | 否 |

- **出参**：object（未强类型，字段见 summary/description）（重新解析任务已提交）
- **鉴权**：OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- POST /api/v1/knowledge/:id/regenerate-summary — （无接口注解，用途由代码反推；实现于 `internal/router/routes_knowledge.go` RegisterKnowledgeRoutes；鉴权 OwnedKnowledgeKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(id)）
- GET /api/v1/knowledge/:id/spans — （无接口注解，用途由代码反推；实现于 `internal/router/routes_knowledge.go` RegisterKnowledgeRoutes；鉴权 Viewer + KBAccessReadFromKnowledgeIDParam(id)）
- GET /api/v1/knowledge/:id/stages — （无接口注解，用途由代码反推；实现于 `internal/router/routes_knowledge.go` RegisterKnowledgeRoutes；与 /spans 共用 handler GetKnowledgeSpans）

### 组织管理

#### GET /api/v1/organizations

**获取我的组织列表**

（无请求参数）

- **出参**：ListOrganizationsResponse
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations

**创建组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 组织信息 | body | CreateOrganizationRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/join

**通过邀请码加入组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 邀请码 | body | JoinOrganizationRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/join-by-id

**通过空间 ID 加入（可搜索空间）**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 空间 ID | body | JoinByOrganizationIDRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/join-request

**提交加入申请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 申请信息 | body | SubmitJoinRequestRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/preview/:code

**通过邀请码预览组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| code | 邀请码 | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/search

**搜索可加入的空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| q | 搜索关键词（空间名称或描述） | query | string | 否 |
| limit | 返回数量限制 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### DELETE /api/v1/organizations/:id

**删除组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id

**获取组织详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### PUT /api/v1/organizations/:id

**更新组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| request | 更新信息 | body | UpdateOrganizationRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/:id/invite

**邀请成员**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| request | 邀请信息 | body | InviteMemberRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/:id/invite-code

**生成邀请码**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id/join-requests

**获取待审核加入申请列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### PUT /api/v1/organizations/:id/join-requests/:request_id/review

**审核加入申请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| request_id | 申请ID | path | string | 是 |
| request | 审核结果 | body | ReviewJoinRequestRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/:id/leave

**退出组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id/members

**获取组织成员列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：ListMembersResponse
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### DELETE /api/v1/organizations/:id/members/:tenant_id

**移除成员**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| tenant_id | 成员空间ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### PUT /api/v1/organizations/:id/members/:tenant_id

**更新成员角色**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| tenant_id | 成员空间ID | path | string | 是 |
| request | 角色信息 | body | UpdateMemberRoleRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### POST /api/v1/organizations/:id/request-upgrade

**申请权限升级**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| request | 申请信息 | body | RequestRoleUpgradeRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id/search-tenants

**Resolve a workspace ID for invitation**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |
| q | Exact workspace ID | query | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id/shared-agents

**获取空间内全部智能体（含我共享的）**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id/shared-knowledge-bases

**获取空间内全部知识库（含我共享的、含智能体携带的）**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/organizations/:id/shares

**获取组织的共享知识库列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织ID | path | string | 是 |

- **出参**：ListSharesResponse
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/agents/:id/shares — （实现于 `internal/router/routes_agent.go` RegisterOrganizationRoutes；鉴权 OwnedAgentOrAdmin）
- POST /api/v1/agents/:id/shares — （同上；鉴权 OwnedAgentOrAdmin）
- POST /api/v1/shared-agents/disabled — （同上；鉴权 Admin）

### Wiki

#### POST /api/v1/knowledgebase/:kb_id/wiki/auto-fix

**Auto-fix wiki issues**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/folders

**List wiki folders**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| parent_id | Parent folder id (empty = root) | query | string | 否 |

- **出参**：WikiFolderListResponse
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledgebase/:kb_id/wiki/folders

**Create a wiki folder**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| folder | Folder data | body | WikiFolderCreateRequest | 是 |

- **出参**：WikiFolder（Created）
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/knowledgebase/:kb_id/wiki/folders/:folder_id

**Delete an empty wiki folder**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| folder_id | Folder ID | path | string | 是 |

- **出参**：无 2xx 响应定义
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledgebase/:kb_id/wiki/folders/:folder_id

**Rename or move a wiki folder**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| folder_id | Folder ID | path | string | 是 |
| folder | Folder update | body | WikiFolderUpdateRequest | 是 |

- **出参**：WikiFolder
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/graph

**Get wiki link graph**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| mode | overview (default) \| ego | query | string | 否 |
| center | Center slug for ego mode | query | string | 否 |
| depth | Ego BFS depth (1-3, default 1) | query | integer | 否 |
| types | Comma-separated page_type allow-list | query | string | 否 |
| limit | Max nodes to return (default 500, max 2000) | query | integer | 否 |

- **出参**：WikiGraphData
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/index

**Get wiki index view**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| types | Comma-separated page types (default: all content types) | query | string | 否 |
| limit | Per-group window size, 1-200 (default 50) | query | integer | 否 |
| cursor | Opaque offset cursor from previous response | query | string | 否 |

- **出参**：WikiIndexResponse
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/issues

**List wiki page issues**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| slug | Filter by page slug | query | string | 否 |
| status | Filter by status (pending, ignored, resolved) | query | string | 否 |

- **出参**：WikiPageIssue[]
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledgebase/:kb_id/wiki/issues/:issue_id/status

**Update wiki page issue status**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| issue_id | Issue ID | path | string | 是 |
| status | New status {'status': 'ignored'} | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/lint

**Run wiki lint**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |

- **出参**：WikiLintReport
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledgebase/:kb_id/wiki/move-page

**Move a wiki page into a folder**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| move | Move target | body | WikiPageMoveRequest | 是 |

- **出参**：WikiPage
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/pages

**List wiki pages**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| page_type | Filter by page type; comma-separated for multiple (e.g. entity,concept) | query | string | 否 |
| status | Filter by status | query | string | 否 |
| query | Full-text search | query | string | 否 |
| page | Page number | query | integer | 否 |
| page_size | Page size | query | integer | 否 |
| sort_by | Sort field | query | string | 否 |
| sort_order | Sort order (asc/desc) | query | string | 否 |

- **出参**：WikiPageListResponse
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledgebase/:kb_id/wiki/pages

**Create a wiki page**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| page | Wiki page data | body | WikiPage | 是 |

- **出参**：WikiPage（Created）
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/knowledgebase/:kb_id/wiki/pages/:slug

**Delete a wiki page**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| slug | Page slug | path | string | 是 |

- **出参**：无 2xx 响应定义
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())。**（待确认：实现用 gin 通配符 `*slug` 而非普通路径参数，见「注解与实现的差异」）**

#### GET /api/v1/knowledgebase/:kb_id/wiki/pages/:slug

**Get a wiki page by slug**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| slug | Page slug | path | string | 是 |

- **出参**：WikiPage
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())。**（待确认：`*slug` 通配符，见「注解与实现的差异」）**

#### PUT /api/v1/knowledgebase/:kb_id/wiki/pages/:slug

**Update a wiki page**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| slug | Page slug | path | string | 是 |
| page | Fields to update | body | WikiPageUpdateRequest | 是 |

- **出参**：WikiPage
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())。**（待确认：`*slug` 通配符，见「注解与实现的差异」）**

#### POST /api/v1/knowledgebase/:kb_id/wiki/rebuild-links

**Rebuild wiki links**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledgebase/:kb_id/wiki/revert

**Revert a wiki page to an earlier revision**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| revert | Revert target | body | WikiPageRevertRequest | 是 |

- **出参**：WikiPage
- **鉴权**：OwnedWikiKBOrAdmin + KBAccessWrite(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/revisions/:slug

**List wiki page revisions**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| slug | Page slug | path | string | 是 |
| version | Return this single revision with content | query | integer | 否 |
| limit | Page size (default 50, max 200) | query | integer | 否 |
| offset | Offset into the newest-first list | query | integer | 否 |

- **出参**：WikiPageRevisionListResponse
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())。**（待确认：`*slug` 通配符，见「注解与实现的差异」）**

#### GET /api/v1/knowledgebase/:kb_id/wiki/search

**Search wiki pages**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |
| q | Search query | query | string | 是 |
| limit | Max results (default 10) | query | integer | 否 |

- **出参**：WikiPage[]
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledgebase/:kb_id/wiki/stats

**Get wiki statistics**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | path | string | 是 |

- **出参**：WikiStats
- **鉴权**：Viewer + KBAccessRead(kb_id)；API Key：apiKeyIngest(apiKeyFullAccess())

### MCP服务

#### POST /api/v1/agent/mcp-oauth-resolutions/:pending_id

**完成对话内 MCP OAuth 授权**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| pending_id | 待授权 ID | path | string | 是 |
| request | {service_id: string} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/agent/mcp-oauth-resolutions/:pending_id/cancel

**跳过对话内 MCP OAuth 授权**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| pending_id | 待授权 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/agent/tool-approvals/:pending_id

**处理 MCP 工具调用待审批请求**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| pending_id | 待审批记录 ID | path | string | 是 |
| request | {decision: ...} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（审批结果）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

#### GET /api/v1/mcp-services

**获取MCP服务列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（MCP服务列表）
- **鉴权**：Viewer；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### POST /api/v1/mcp-services

**创建MCP服务**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | MCP服务配置 | body | MCPService | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的MCP服务）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### GET /api/v1/mcp-oauth/callback

> ⚠ swagger 注解写的是 `/mcp-services/oauth/callback`，但代码把它注册在 v1 根组。**上面是真实可调用路径**；缺陷见「注解与实现的差异」A2。

**MCP OAuth 回调**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| code | 授权码 | query | string | 否 |
| state | 状态参数 | query | string | 否 |
| error | 授权错误码 | query | string | 否 |

- **出参**：无（Found）
- **鉴权**：⚠️ 该路径在路由树中不存在（真实路径为 `/api/v1/mcp-oauth/callback`），见「注解与实现的差异」。真实路由鉴权：公开（OAuth state 参数自校验）；API Key：不适用

#### DELETE /api/v1/mcp-services/:id

**删除MCP服务**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### GET /api/v1/mcp-services/:id

**获取MCP服务详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（MCP服务详情）
- **鉴权**：Viewer；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### PUT /api/v1/mcp-services/:id

**更新MCP服务**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |
| request | 更新字段 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的MCP服务）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### PUT /api/v1/mcp-services/:id/credentials

**设置 MCP 服务凭据**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP 服务 ID | path | string | 是 |
| request | {api_key?: string, token?: string} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（写入后的凭据状态）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### DELETE /api/v1/mcp-services/:id/credentials/:field

**移除 MCP 服务的单个凭据字段**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP 服务 ID | path | string | 是 |
| field | 字段名（api_key \| token） | path | string | 是 |

- **出参**：无 2xx 响应定义
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### GET /api/v1/mcp-services/:id/metadata

**读取已保存的 MCP 工具目录**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（目录快照）
- **鉴权**：Viewer；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### POST /api/v1/mcp-services/:id/metadata/refresh

**同步 MCP 工具目录**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（同步后的目录快照）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### POST /api/v1/mcp-services/:id/oauth/authorize-url

**发起 MCP OAuth 授权**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP 服务 ID | path | string | 是 |
| request | {redirect_uri: string, frontend_redirect?: string} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（{authorization_url, authorization_attempt}）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### GET /api/v1/mcp-services/:id/oauth/status

**查询 MCP OAuth 授权状态**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP 服务 ID | path | string | 是 |
| authorization_attempt | 本次授权尝试 ID；传入后不会接受历史 Token | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（{authorized, state, refresh_available, expires_at?}）
- **鉴权**：Viewer；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### DELETE /api/v1/mcp-services/:id/oauth/token

**撤销 MCP OAuth 授权**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP 服务 ID | path | string | 是 |

- **出参**：无 2xx 响应定义
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### GET /api/v1/mcp-services/:id/resources

**获取MCP服务资源列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（资源列表）
- **鉴权**：Viewer；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### POST /api/v1/mcp-services/:id/test

**测试MCP服务连接**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（测试结果）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### PUT /api/v1/mcp-services/:id/tool-approvals/:tool_name

**设置 MCP 工具策略**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP 服务 ID | path | string | 是 |
| tool_name | 工具名 | path | string | 是 |
| request | {require_approval?: bool, enabled?: bool} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新结果）
- **鉴权**：Admin；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

#### GET /api/v1/mcp-services/:id/tools

**获取MCP服务工具列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | MCP服务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（工具列表）
- **鉴权**：Viewer；API Key：apiKeyManageMCPServices(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/mcp-services/:id/tool-approvals — （实现于 `internal/router/routes_infra.go` RegisterMCPServiceRoutes；鉴权 Viewer）
- POST /api/v1/mcp-services/:id/usage-instructions/generate — （同上；鉴权 Admin）

### 认证

#### POST /api/v1/auth/auto-setup

**自动初始化（Lite 桌面版）**

（无请求参数）

- **出参**：LoginResponse
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/change-password

**修改密码**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 密码修改请求 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（修改成功）
- **鉴权**：需认证，无角色下限；API Key：未声明（不可通过 API Key，除 auth/me GET 外）

#### GET /api/v1/auth/config

**获取认证配置**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（认证配置）
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/invitations/lookup

**解析共享邀请链接 token**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 邀请 token | body | invitationLookupRequest | 是 |

- **出参**：invitationLookupResponse
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/login

**用户登录**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 登录请求参数 | body | LoginRequest | 是 |

- **出参**：LoginResponse
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/logout

**用户登出**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（登出成功）
- **鉴权**：需认证，无角色下限；API Key：未声明（不可通过 API Key，除 auth/me GET 外）

#### GET /api/v1/auth/me

**获取当前用户信息**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（用户信息）
- **鉴权**：需认证，无角色下限；API Key：apiKeyAny()

#### PUT /api/v1/auth/me/preferences

**更新当前用户的个性化设置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Preferences patch | body | updateMyPreferencesRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的偏好）
- **鉴权**：需认证，无角色下限；API Key：未声明（不可通过 API Key，除 auth/me GET 外）

#### GET /api/v1/auth/oidc/callback

**OIDC登录重定向回调**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| code | OIDC授权码 | query | string | 否 |
| state | OIDC状态 | query | string | 否 |
| error | OIDC错误码 | query | string | 否 |

- **出参**：无（Found）
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### GET /api/v1/auth/oidc/config

**获取OIDC登录配置**

（无请求参数）

- **出参**：OIDCConfigResponse
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### GET /api/v1/auth/oidc/start

**发起 OIDC 登录（直接 302）**

（无请求参数）

- **出参**：无（Found）
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### GET /api/v1/auth/oidc/url

**获取OIDC授权地址**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| redirect_uri | OIDC回调地址 | query | string | 是 |

- **出参**：OIDCAuthURLResponse
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/refresh

**刷新令牌**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 刷新令牌 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（新令牌）
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/register

**用户注册**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 注册请求参数 | body | RegisterRequest | 是 |

- **出参**：RegisterResponse（Created）
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/register-by-invite

**使用共享链接注册**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 邀请注册请求 | body | registerByInviteRequest | 是 |

- **出参**：LoginResponse（Created）
- **鉴权**：公开（noAuthAPI 白名单，无需认证）；API Key：不适用

#### POST /api/v1/auth/switch-tenant

**切换激活空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 切换请求 | body | object | 是 |

- **出参**：LoginResponse
- **鉴权**：需认证，无角色下限；API Key：未声明（不可通过 API Key，除 auth/me GET 外）

#### GET /api/v1/auth/validate

**验证令牌**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（令牌有效）
- **鉴权**：需认证，无角色下限；API Key：未声明（不可通过 API Key，除 auth/me GET 外）

### 初始化

#### POST /api/v1/initialization/asr/check

**检查ASR模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | ASR检查请求 | body | ModelTestRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（检查结果）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/initialization/config/:kbId

**获取知识库配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kbId | 知识库ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（配置信息）
- **鉴权**：Viewer + KBAccessRead(kbId)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### PUT /api/v1/initialization/config/:kbId

**更新知识库配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kbId | 知识库ID | path | string | 是 |
| request | 配置请求 | body | KBModelConfigRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKBOrAdminFromKbIDParam + KBAccessWrite(kbId)；API Key：apiKeyManageKnowledgeBases(apiKeyFullAccess())

#### POST /api/v1/initialization/embedding/test

**测试Embedding模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Embedding测试请求 | body | ModelTestRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（测试结果）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/extract/fabri-tag

**生成随机标签**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（生成的标签）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/extract/fabri-text

**生成示例文本**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 生成请求 | body | FabriTextRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（生成的文本）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/extract/text-relation

**提取文本关系**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 提取请求 | body | TextRelationExtractionRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（提取结果）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/initialize/:kbId

**初始化知识库配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kbId | 知识库ID | path | string | 是 |
| request | 初始化请求 | body | InitializationRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（初始化成功）
- **鉴权**：OwnedKBOrAdminFromKbIDParam + KBAccessWrite(kbId)；API Key：apiKeyManageKnowledgeBases(apiKeyFullAccess())

#### POST /api/v1/initialization/multimodal/test

**测试多模态功能**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| image | 测试图片 | formData | file | 是 |
| vlm_model | VLM模型名称 | formData | string | 是 |
| vlm_base_url | VLM Base URL | formData | string | 是 |
| vlm_api_key | VLM API Key | formData | string | 否 |
| vlm_interface_type | VLM接口类型 | formData | string | 否 |
| storage_type | 存储类型(cos/minio) | formData | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（测试结果）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/initialization/ollama/download/progress/:taskId

**获取下载进度**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| taskId | 任务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（下载进度）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/initialization/ollama/download/tasks

**列出下载任务**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（任务列表）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/initialization/ollama/models

**列出Ollama模型**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（模型列表）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/ollama/models/check

**检查Ollama模型状态**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 模型名称列表 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（模型状态）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/ollama/models/download

**下载Ollama模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 模型名称 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（下载任务信息）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/initialization/ollama/status

**检查Ollama服务状态**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（Ollama状态）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/remote/check

**检查远程模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 模型检查请求 | body | RemoteModelCheckRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（检查结果）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/initialization/rerank/check

**检查Rerank模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Rerank检查请求 | body | ModelTestRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（检查结果）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

### SandboxConfig

#### GET /api/v1/sandbox-configs

**List sandbox configs**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（Sandbox configs and defaults）
- **鉴权**：Viewer；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/sandbox-configs

**Create sandbox config**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Sandbox backend config | body | sandboxConfigRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created sandbox config）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### DELETE /api/v1/sandbox-configs/:id

**Delete sandbox config**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| force | Force delete when inventory is unverifiable | query | boolean | 否 |

- **出参**：object（未强类型，字段见 summary/description）（Deletion success）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id

**Get sandbox config**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Sandbox config）
- **鉴权**：Viewer；API Key：apiKeyFullAccess（未叠加细分能力位）

#### PUT /api/v1/sandbox-configs/:id

**Update sandbox config**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| request | Updated sandbox config | body | sandboxConfigRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Updated sandbox config）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/sandboxes

**Inspect sandbox config inventory**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Sandbox inventory）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/skills

**List installed skills**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Installed skills）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/sandbox-configs/:id/skills

**Install a skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| file | Skill bundle (zip) | formData | file | 否 |
| request | Install from a registry, git host, or archive URL | body | skillSourceRequest | 否 |

- **出参**：object（未强类型，字段见 summary/description）（Install accepted）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### DELETE /api/v1/sandbox-configs/:id/skills/:skillId

**Remove an installed skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Removal accepted）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/skills/:skillId

**Get an installed skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Installed skill）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### PATCH /api/v1/sandbox-configs/:id/skills/:skillId

**Update an installed skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |
| request | Fields to update | body | skillPatchRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Updated skill）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/skills/:skillId/files

**List files of an installed skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Skill files）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/skills/:skillId/files/content

**Read one file of an installed skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |
| path | Skill-root-relative file path | query | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Skill file）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/skills/:skillId/install-events

**Follow an install or removal**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：string（SSE stream of progress events）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/sandbox-configs/:id/skills/:skillId/reinstall

**Retry a skill install**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Reinstall accepted）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/sandbox-configs/:id/skills/:skillId/stop

**Stop a skill install**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Stopped skill）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/sandbox-configs/:id/skills/:skillId/transcript

**Follow an install's agent transcript**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Sandbox config ID | path | string | 是 |
| skillId | Skill ID | path | string | 是 |

- **出参**：string（SSE stream of transcript events）
- **鉴权**：Admin；API Key：apiKeyFullAccess（未叠加细分能力位）

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/sandbox-configs/:id/skills/:skillId/guidance — （鉴权 Admin）**（待确认：与 POST 同名端点动词语义需核实）**
- POST /api/v1/sandbox-configs/:id/skills/:skillId/guidance — （鉴权 Admin）
- POST /api/v1/sandbox-configs/templates/query — （鉴权 Admin）
- PUT /api/v1/sandbox-configs/workspace-policy — （鉴权 Admin）

### 长期记忆

#### POST /api/v1/memory/consolidate

**立刻整理我的记忆**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（整理结果）
- **鉴权**：Viewer（挂在 `/memory` 分组级别，含全部读写操作）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/memory/documents

**列出常用资料**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| limit | 每页条数 | query | integer | 否 |
| offset | 偏移量 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）（文档列表）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### DELETE /api/v1/memory/documents/:id

**停止用某份文档做个性化检索**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 亲和度 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/memory/export

**导出我的记忆**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（记忆导出）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### DELETE /api/v1/memory/items

**清空我的记忆**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（清空成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/memory/items

**列出我的记忆**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| status | 状态过滤 | query | string | 否 |
| limit | 每页条数 | query | integer | 否 |
| offset | 偏移量 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）（记忆列表）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/memory/items

**新增一条记忆**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 记忆内容 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（新增的记忆）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### DELETE /api/v1/memory/items/:id

**删除一条记忆**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 记忆ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### PUT /api/v1/memory/items/:id

**修改一条记忆**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 记忆ID | path | string | 是 |
| request | 记忆内容 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的记忆）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/memory/items/:id/confirm

**确认一条推断出的记忆**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 记忆 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（确认成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/memory/items/:id/reject

**否决一条推断出的记忆**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 记忆 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（否决成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/memory/settings

**获取我的记忆设置**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（记忆设置）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### PUT /api/v1/memory/settings

**更新我的记忆设置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 设置 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的设置）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### GET /api/v1/memory/topics

**列出正在观察的主题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| limit | 每页条数 | query | integer | 否 |
| offset | 偏移量 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）（主题列表）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### DELETE /api/v1/memory/topics/:id

**停止跟踪一个主题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 主题 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

#### POST /api/v1/memory/topics/:id/promote

**立即记为长期关注**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 主题 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（新增的记忆）
- **鉴权**：Viewer（同上）；API Key：apiKeyFullAccess（未叠加细分能力位）

### DataSource

#### GET /api/v1/datasource

**List data sources for a knowledge base**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| kb_id | Knowledge base ID | query | string | 是 |

- **出参**：DataSource[]
- **鉴权**：Viewer；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource

**Create a new data source**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Data source configuration | body | DataSource | 是 |

- **出参**：DataSource（Created）
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### GET /api/v1/datasource/logs/:log_id

**Get specific sync log**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| log_id | Sync log ID | path | string | 是 |

- **出参**：SyncLog
- **鉴权**：Viewer；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### GET /api/v1/datasource/types

**Get available connectors**

（无请求参数）

- **出参**：ConnectorMetadata[]
- **鉴权**：Viewer；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource/validate-credentials

**Test connection with raw credentials (no persistence)**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | type and credentials | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### DELETE /api/v1/datasource/:id

**Delete a data source**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |

- **出参**：无 2xx 响应定义
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### GET /api/v1/datasource/:id

**Get a data source by ID**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |

- **出参**：DataSource
- **鉴权**：Viewer；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### PUT /api/v1/datasource/:id

**Update a data source**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |
| request | Updated configuration | body | DataSource | 是 |

- **出参**：DataSource
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### GET /api/v1/datasource/:id/logs

**Get sync logs**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |
| limit | Limit (default: 10) | query | integer | 否 |
| offset | Offset (default: 0) | query | integer | 否 |

- **出参**：SyncLog[]
- **鉴权**：Viewer；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource/:id/pause

**Pause data source**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource/:id/resource-ancestors

**Resolve resource ancestors**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |
| request | Resource IDs to resolve | body | resolveAncestorsRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### GET /api/v1/datasource/:id/resources

**List available resources in data source**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |
| parent_id | Parent resource ExternalID; empty lists the top level | query | string | 否 |

- **出参**：Resource[]
- **鉴权**：Viewer；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource/:id/resume

**Resume data source**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource/:id/sync

**Trigger immediate sync**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |

- **出参**：SyncLog
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

#### POST /api/v1/datasource/:id/validate

**Test data source connection**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Data source ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageDataSources(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- PUT /api/v1/datasource/:id/credentials — （鉴权 Admin）
- DELETE /api/v1/datasource/:id/credentials/:field — （鉴权 Admin）

### 会话

#### GET /api/v1/sessions

**获取会话列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| page | 页码 | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |
| keyword | 标题模糊搜索 | query | string | 否 |
| source | 来源过滤：web/embed/api/feishu/wechat/slack/...（api、embed、IM 渠道需 Admin+） | query | string | 否 |
| agent_id | 按 Agent 过滤（仅对 IM 会话生效） | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（会话列表）
- **鉴权**：Viewer（挂在 sessions 分组 `r.Group` 级别，个人会话对象由上下文限定）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions

**创建会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 会话创建请求 | body | CreateSessionRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的会话）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### DELETE /api/v1/sessions/batch

**批量删除会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 批量删除请求 | body | batchDeleteRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除结果）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### DELETE /api/v1/sessions/:id

**删除会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### GET /api/v1/sessions/:id

**获取会话详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（会话详情）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### PUT /api/v1/sessions/:id

**更新会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话ID | path | string | 是 |
| request | 会话信息 | body | Session | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的会话）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### DELETE /api/v1/sessions/:id/messages

**清空会话消息**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（清空成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### DELETE /api/v1/sessions/:id/pin

**取消置顶会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（取消置顶成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### GET /api/v1/sessions/:session_id/artifacts

**列出会话生成的产物文件**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())。**（待确认：swagger 路径参数名 `session_id`，实现是 `:id`，见「注解与实现的差异」）**

#### POST /api/v1/sessions/:session_id/fork

**分叉会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 源会话 ID | path | string | 是 |
| request | 分叉请求 | body | ForkSessionRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（新会话）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### GET /api/v1/sessions/:session_id/messages/:message_id/suggestions

**获取回答后推荐问题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话 ID | path | string | 是 |
| message_id | 助手消息 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())。**（待确认：swagger 参数名 `session_id`，实现是 `:id`）**

#### POST /api/v1/sessions/:session_id/messages/:message_id/suggestions

**确保生成回答后推荐问题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话 ID | path | string | 是 |
| message_id | 助手消息 ID | path | string | 是 |
| request | 生成选项 | body | EnsureMessageSuggestionsRequest | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions/:session_id/pin

**置顶会话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（置顶成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions/:session_id/suggestion-events

**上报推荐问题事件**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话 ID | path | string | 是 |
| request | 事件 | body | SuggestionEventRequest | 是 |

- **出参**：无 2xx 响应定义
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions/:session_id/generate_title

> ⚠ swagger 注解写的是 `/sessions/{session_id}/title`，漏了 `generate_` 前缀。**上面是真实可调用路径**；缺陷见「注解与实现的差异」A3。

**生成会话标题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |
| request | 生成请求 | body | GenerateTitleRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（生成的标题）
- **鉴权**：⚠️ 该路径在路由树中不存在（真实路径为 `.../generate_title`），见「注解与实现的差异」。真实端点鉴权：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/artifacts — （鉴权 Viewer，`apiKeyChat`）
- GET /api/v1/sessions/:id/attachments — （同上）
- DELETE /api/v1/sessions/:id/attachments/:attachment_id — （同上）
- GET /api/v1/sessions/:id/attachments/:attachment_id — （同上）
- GET /api/v1/sessions/:id/attachments/:attachment_id/preview — （同上）
- GET /api/v1/sessions/:id/local-browser — （同上）
- GET /api/v1/sessions/:id/sandbox/desktop — （需认证 + 一次性 ticket 校验，WS 升级）
- GET /api/v1/sessions/:id/sandbox/terminal — （同上）
- POST /api/v1/sessions/:session_id/attachments — （鉴权 Viewer，`apiKeyChat`）
- POST /api/v1/sessions/:session_id/local-browser — （同上）
- POST /api/v1/sessions/:session_id/sandbox/desktop-ticket — （同上）
- POST /api/v1/sessions/:session_id/sandbox/desktop/activity — （同上）
- POST /api/v1/sessions/:session_id/sandbox/terminal-ticket — （同上）

### System Admin

#### GET /api/v1/system/admin/api-keys

**List platform API keys**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/system/admin/api-keys

**Create a platform API key**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Platform API key | body | platformAPIKeyCreateRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### DELETE /api/v1/system/admin/api-keys/:key_id

**Revoke a platform API key**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| key_id | API key ID | path | integer | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### GET /api/v1/system/admin/list

**List all system administrators**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| offset | Page offset | query | integer | 否 |
| limit | Page size (max 200) | query | integer | 否 |

- **出参**：ListSystemAdminsResponse
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/system/admin/promote

**Promote a user to system administrator**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | User promotion request | body | PromoteUserToSystemAdminRequest | 是 |

- **出参**：UserInfo
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/system/admin/revoke

**Revoke system administrator privileges from a user**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | User revocation request | body | RevokeSystemAdminRequest | 是 |

- **出参**：UserInfo
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### DELETE /api/v1/system/admin/runtime/queues/:queue/archived

**Purge all archived tasks in a queue**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| queue | Queue name | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_runtime_manage)

#### GET /api/v1/system/admin/runtime/queues/:queue/tasks

**List runtime queue tasks by state**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| queue | Queue name | path | string | 是 |
| state | Task state | query | string | 是 |
| cursor | Opaque continuation cursor | query | string | 否 |
| page_size | Page size | query | integer | 否 |

- **出参**：RuntimeTasksResponse
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_runtime_read, system_runtime_manage)

#### POST /api/v1/system/admin/runtime/queues/:queue/tasks/:task_id/actions/:action

**Run a safe runtime task action**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| queue | Queue name | path | string | 是 |
| task_id | Task ID | path | string | 是 |
| action | Action | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_runtime_manage)

#### DELETE /api/v1/system/admin/settings/:key

**Reset a system setting to ENV / built-in default**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| key | Setting key | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Reset acknowledged）
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_settings_manage)

#### GET /api/v1/system/admin/settings/:key

**Get a single system setting by key**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| key | Setting key (e.g. file.max_size_mb) | path | string | 是 |

- **出参**：SystemSetting
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_settings_read, system_settings_manage)

#### PUT /api/v1/system/admin/settings/:key

**Update a system setting value**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| key | Setting key | path | string | 是 |
| request | New value | body | UpdateSystemSettingRequest | 是 |

- **出参**：SystemSetting
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_settings_manage)

#### POST /api/v1/system/admin/tenants/apply-default-storage-quota

**Apply the default storage quota to every existing workspace**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（{affected, quota_bytes}）
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_tenants_manage)

#### POST /api/v1/system/admin/users/create

**Create a new user (SystemAdmin)**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | User creation request | body | AdminCreateUserRequest | 是 |

- **出参**：CreateSystemUserResponse
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/system/admin/users/reset-password

**Reset another user's password**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Password reset request | body | ResetUserPasswordRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：SystemAdmin；API Key：未声明（不可通过 API Key 调用）

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/system/admin/settings — （鉴权 SystemAdmin；API Key：apiKeyPlatform(system_settings_read, system_settings_manage)）

### 空间管理

#### GET /api/v1/tenants

**获取空间列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（空间列表）
- **鉴权**：需认证，无角色下限（列出可见空间）；API Key：apiKeyManageTenantSettings(apiKeyFullAccess())

#### POST /api/v1/tenants

**创建空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 空间信息 | body | createTenantRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的空间，可选含 api_key）
- **鉴权**：需认证，无角色下限（自助创建空间）；API Key：apiKeyPlatform(system_tenants_manage)

#### GET /api/v1/tenants/all

**获取所有空间列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：CrossTenant；API Key：apiKeyPlatform(system_tenants_read, system_tenants_manage)

#### （非独立端点）提示词模板 —— 经 `GET /api/v1/tenants/kv/:key` 取用

> ⚠ 这不是一个真实路由。代码里只有通用的 `GET /api/v1/tenants/kv/:key`，由 handler 按 `key` 值内部分发；子函数误加了一份 `@Router` 注解才在 swagger 里显形。调用方式：`GET /api/v1/tenants/kv/prompt-templates` 走的仍是通用路由。见「注解与实现的差异」B4。

**获取提示词模板**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：⚠️ 幽灵端点，无独立路由（是通用 `GET /tenants/kv/:key` 的一个 key 值），见「注解与实现的差异」。真实路由鉴权：Viewer；API Key：apiKeyManageTenantSettings(apiKeyFullAccess())

#### （非独立端点）网络搜索配置 —— 经 `GET /api/v1/tenants/kv/:key` 取用

> ⚠ 同上，非真实路由，由 `GET /api/v1/tenants/kv/:key` 内部分发。见「注解与实现的差异」B5。

**获取空间网络搜索配置**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：⚠️ 同上，幽灵端点，见「注解与实现的差异」

#### GET /api/v1/tenants/kv/:key

**获取空间KV配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| key | 配置键名 | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（配置值）
- **鉴权**：Viewer；API Key：apiKeyManageTenantSettings(apiKeyFullAccess())

#### PUT /api/v1/tenants/kv/:key

**更新空间KV配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| key | 配置键名 | path | string | 是 |
| request | 配置值 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：Admin；API Key：apiKeyManageTenantSettings(apiKeyFullAccess())

#### GET /api/v1/tenants/search

**搜索空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| keyword | 搜索关键词 | query | string | 否 |
| tenant_id | 空间ID筛选 | query | integer | 否 |
| page | 页码 | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：CrossTenant；API Key：apiKeyPlatform(system_tenants_read, system_tenants_manage)

#### DELETE /api/v1/tenants/:id

**删除空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | integer | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyPlatform(system_tenants_manage)

#### GET /api/v1/tenants/:id

**获取空间详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | integer | 是 |

- **出参**：object（未强类型，字段见 summary/description）（空间详情）
- **鉴权**：PathTenantMatch + Viewer；API Key：apiKeyPlatform(system_tenants_read, system_tenants_manage)

#### PUT /api/v1/tenants/:id

**更新空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | integer | 是 |
| request | 空间信息 | body | Tenant | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的空间）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyPlatform(system_tenants_manage)

#### GET /api/v1/tenants/:id/api-principal-config

**获取空间 API Key 用户身份配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | integer | 是 |

- **出参**：object（未强类型，字段见 summary/description）（API principal 配置）
- **鉴权**：PathTenantMatch + Owner；API Key：未声明（不可通过 API Key 调用）

#### PUT /api/v1/tenants/:id/api-principal-config

**更新空间 API Key 用户身份配置**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | integer | 是 |
| request | API principal 配置 | body | apiPrincipalConfigRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的配置）
- **鉴权**：PathTenantMatch + Owner；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/tenants/:id/api-principal-test-token

**生成 API Playground 测试 JWT**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | integer | 是 |
| request | 测试 Token 参数 | body | apiPrincipalTestTokenRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（短期 JWT）
- **鉴权**：PathTenantMatch + Owner；API Key：未声明（不可通过 API Key 调用）

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/tenants/:id/api-keys — （鉴权 PathTenantMatch + Owner；`apiKeyManageMembers`? 不，见下方精确值：未声明——不可通过 API Key 调用）
- POST /api/v1/tenants/:id/api-keys — （同上，PathTenantMatch + Owner，未声明）
- DELETE /api/v1/tenants/:id/api-keys/:key_id — （同上）
- PUT /api/v1/tenants/:id/api-keys/:key_id — （同上）

### FAQ管理

#### GET /api/v1/faq/import/progress/:task_id

**获取FAQ导入进度**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| task_id | 任务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（导入进度）
- **鉴权**：Viewer；API Key：apiKeyRetrieve(apiKeyIngest(apiKeyFullAccess()))

#### DELETE /api/v1/knowledge-bases/:id/faq/entries

**批量删除FAQ条目**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 要删除的FAQ ID列表(seq_id) | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/faq/entries

**获取FAQ条目列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| page | 页码 | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |
| tag_id | 标签ID筛选(seq_id)，兼容旧版单标签 | query | integer | 否 |
| tag_ids | 标签UUID筛选，逗号分隔（OR语义） | query | string | 否 |
| keyword | 关键词搜索 | query | string | 否 |
| search_field | 搜索字段: standard_question/similar_questions/answers，默认全部 | query | string | 否 |
| sort_order | 排序方式: asc，默认按更新时间倒序 | query | string | 否 |
| is_enabled | 启用状态筛选；不传时返回全部 | query | boolean | 否 |

- **出参**：object（未强类型，字段见 summary/description）（FAQ列表）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/faq/entries

**批量更新/插入FAQ条目**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 批量操作请求 | body | FAQBatchUpsertPayload | 是 |

- **出参**：object（未强类型，字段见 summary/description）（任务ID）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/faq/entries/export

**导出FAQ条目**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| format | 导出格式：csv（默认）或 json | query | string | 否 |

- **出参**：file（导出文件）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id/faq/entries/fields

**批量更新FAQ字段**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 字段更新请求 | body | FAQEntryFieldsBatchUpdate | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id/faq/entries/tags

**批量更新FAQ标签**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 标签更新请求 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/faq/entries/:entry_id

**获取FAQ条目详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| entry_id | FAQ条目ID(seq_id) | path | integer | 是 |

- **出参**：object（未强类型，字段见 summary/description）（FAQ条目详情）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id/faq/entries/:entry_id

**更新FAQ条目**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| entry_id | FAQ条目ID(seq_id) | path | integer | 是 |
| request | FAQ条目 | body | FAQEntryPayload | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/faq/entries/:entry_id/similar-questions

**添加相似问**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| entry_id | FAQ条目ID(seq_id) | path | integer | 是 |
| request | 相似问列表 | body | addSimilarQuestionsRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的FAQ条目）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/faq/entry

**创建单个FAQ条目**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | FAQ条目 | body | FAQEntryPayload | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的FAQ条目）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id/faq/import/last-result/display

**更新FAQ最后一次导入结果显示状态**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 状态更新请求 | body | updateLastFAQImportResultDisplayStatusRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/faq/search

**搜索FAQ**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 搜索请求 | body | FAQSearchRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（搜索结果）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

### 知识库

#### GET /api/v1/knowledge-bases

**获取知识库列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| agent_id | 共享智能体 ID（传入时返回该智能体可用的知识库） | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（知识库列表）
- **鉴权**：Viewer；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases

**创建知识库**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 知识库信息 | body | KnowledgeBase | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的知识库）
- **鉴权**：Contributor；API Key：apiKeyRetrieve(apiKeyFullAccess())（组默认位，创建未额外要求 manage_kbs——见待确认清单）

#### POST /api/v1/knowledge-bases/copy

**复制知识库**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 复制请求 | body | CopyKnowledgeBaseRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（任务ID）
- **鉴权**：Contributor；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/copy/progress/:task_id

**获取知识库复制进度**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| task_id | 任务ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（进度信息）
- **鉴权**：Viewer；API Key：apiKeyRetrieve(apiKeyManageKnowledgeBases(apiKeyFullAccess()))（`.With` 覆盖组默认位）。**注**：此路由被中间产物 `api_routes.json` 的提取脚本漏抓（见「注解与实现的差异」），但实际存在且与本文档一致。

#### DELETE /api/v1/knowledge-bases/:id

**删除知识库**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id

**获取知识库详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| agent_id | 共享智能体 ID（用于校验智能体是否有权访问该知识库） | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（知识库详情）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id

**更新知识库**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 更新请求 | body | UpdateKnowledgeBaseRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的知识库）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/activity

**获取知识库活动记录**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| after_id | 游标：返回 id 小于此值的记录 | query | integer | 否 |
| limit | 页大小，1-100，默认 50 | query | integer | 否 |
| action | 按 action 精确过滤 | query | string | 否 |
| outcome | 按 outcome 精确过滤 | query | string | 否 |
| actor | 按 actor_user_id 精确过滤 | query | string | 否 |

- **出参**：auditLogListResponse
- **鉴权**：OwnedKBOrAdmin + KBAccessRead(id)；API Key：未声明（不可通过 API Key 调用，JWT-only）

#### POST /api/v1/knowledge-bases/:id/duplicate

**创建知识库副本**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 源知识库 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建后的知识库副本）
- **鉴权**：Contributor + KBAccessRead(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/hybrid-search

**混合搜索**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 搜索参数 | body | SearchParams | 是 |
| resource_urls | 文件引用形式，public 返回可加载直链 | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（搜索结果）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/hybrid-search

**混合搜索**

（同上，GET 版为兼容旧客户端保留，两者参数/鉴权一致）

- **出参**：object（未强类型，字段见 summary/description）（搜索结果）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### GET /api/v1/knowledge-bases/:id/move-targets

**获取可移动目标知识库列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 源知识库 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（可移动目标列表）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### PUT /api/v1/knowledge-bases/:id/pin

**置顶/取消置顶知识库**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的知识库）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyRetrieve(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- POST /api/v1/knowledge-bases/:id/profile/generate — （鉴权 OwnedKBOrAdmin + KBAccessWrite(id)）

### 问答

#### POST /api/v1/agent-chat/:session_id

**Agent问答**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |
| request | 问答请求 | body | CreateKnowledgeQARequest | 是 |
| resource_urls | 文件引用形式，public 返回可加载直链 | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（问答结果，SSE 流）
- **鉴权**：Viewer（挂在 agent-chat 分组级别）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/knowledge-chat/:session_id

**知识问答**

（参数同上）

- **出参**：object（未强类型，字段见 summary/description）（问答结果，SSE 流）
- **鉴权**：Viewer（挂在 knowledge-chat 分组级别）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/knowledge-search

**知识搜索**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 搜索请求 | body | SearchKnowledgeRequest | 是 |
| resource_urls | 文件引用形式，public 返回可加载直链 | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（搜索结果）
- **鉴权**：Viewer（挂在 knowledge-search 分组级别）；API Key：apiKeyRetrieve(apiKeyFullAccess())

#### GET /api/v1/sessions/continue-stream/:session_id

**继续流式响应**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |
| message_id | 消息ID | query | string | 是 |
| resource_urls | 文件引用形式，public 返回可加载直链 | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（流式响应）
- **鉴权**：Viewer（挂在 sessions 分组级别）；API Key：apiKeyChat(apiKeyFullAccess())

#### GET /api/v1/sessions/:id/steer

**列出当前运行中尚未消费的排队消息**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### DELETE /api/v1/sessions/:id/steer/:steer_id

**删除一条排队中的消息**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 会话 ID | path | string | 是 |
| steer_id | 排队消息 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions/:session_id/steer

**向运行中的对话追加消息**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话 ID | path | string | 是 |
| request | 追加消息 | body | SteerMessageRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（queued \| new_run）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions/:session_id/steer/:steer_id/inject

**将排队消息改为立即注入**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话 ID | path | string | 是 |
| steer_id | 排队消息 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（queued \| new_run）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

#### POST /api/v1/sessions/:session_id/stop

**停止生成**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |
| request | 停止请求 | body | StopSessionRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（停止成功）
- **鉴权**：Viewer（同上）；API Key：apiKeyChat(apiKeyFullAccess())

### 智能体

#### GET /api/v1/agents

**获取智能体列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（智能体列表）
- **鉴权**：Viewer；API Key：apiKeyFullAccess（agents 组，未叠加细分能力位）

#### POST /api/v1/agents

**创建智能体**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 智能体信息 | body | CreateAgentRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的智能体）
- **鉴权**：Contributor；API Key：apiKeyFullAccess

#### GET /api/v1/agents/placeholders

**获取占位符定义**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（占位符定义）
- **鉴权**：Viewer；API Key：apiKeyFullAccess（agents 组，未叠加细分能力位）

#### GET /api/v1/agents/type-presets

**获取智能体类型预设列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（预设列表）
- **鉴权**：Viewer；API Key：apiKeyFullAccess（agents 组，未叠加细分能力位）

#### DELETE /api/v1/agents/:id

**删除智能体**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 智能体ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedAgentOrAdmin；API Key：apiKeyFullAccess

#### GET /api/v1/agents/:id

**获取智能体详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 智能体ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（智能体详情）
- **鉴权**：Viewer；API Key：apiKeyFullAccess（agents 组，未叠加细分能力位）

#### PUT /api/v1/agents/:id

**更新智能体**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 智能体ID | path | string | 是 |
| request | 更新请求 | body | UpdateAgentRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的智能体）
- **鉴权**：OwnedAgentOrAdmin；API Key：apiKeyFullAccess

#### POST /api/v1/agents/:id/copy

**复制智能体**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 智能体ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（复制成功）
- **鉴权**：Contributor；API Key：apiKeyFullAccess

#### GET /api/v1/agents/:id/suggested-questions

**获取推荐问题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 智能体ID | path | string | 是 |
| knowledge_base_ids | 知识库ID列表（逗号分隔），覆盖智能体默认配置 | query | string | 否 |
| knowledge_ids | 知识ID列表（逗号分隔），限定到具体文档 | query | string | 否 |
| tag_scopes | 带知识库归属的标签范围（JSON） | query | string | 否 |
| limit | 返回数量上限（未传时使用智能体配置的开场问题数量，最大30） | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）（推荐问题列表）
- **鉴权**：Viewer；API Key：apiKeyReadAgents(apiKeyManageAgents(apiKeyChat(apiKeyFullAccess())))

### StorageBackend

#### GET /api/v1/storage-backends

**List storage backends**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（列表 + default_storage_backend_id）
- **鉴权**：Viewer；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### POST /api/v1/storage-backends

**Create storage backend**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Storage backend configuration | body | storageBackendRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：Admin；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### POST /api/v1/storage-backends/test

**Test storage backend with raw config**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Storage backend configuration to test | body | storageBackendRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（success, error）
- **鉴权**：Admin；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### GET /api/v1/storage-backends/types

**List allowed storage provider types**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### DELETE /api/v1/storage-backends/:id

**Delete storage backend**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Storage backend ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### GET /api/v1/storage-backends/:id

**Get storage backend**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Storage backend ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### PUT /api/v1/storage-backends/:id

**Update storage backend**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Storage backend ID | path | string | 是 |
| request | Updated storage backend fields | body | storageBackendRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### PUT /api/v1/storage-backends/:id/default

**Set default storage backend**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Storage backend ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

#### POST /api/v1/storage-backends/:id/test

**Test storage backend by ID**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Storage backend ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageStorageBackends(apiKeyFullAccess())

### 系统

#### GET /api/v1/system/capabilities

**获取部署能力清单**

（无请求参数）

- **出参**：object（标准 code/msg/data 包装，data 为 DeploymentCapabilitiesData）
- **鉴权**：Viewer；API Key：apiKeyAny()（`.With` 覆盖组默认 apiKeyManageVectorStores）

#### POST /api/v1/system/docreader/reconnect

**重连文档解析服务**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | DocReader 地址 | body | object | 是 |

- **出参**：无
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### GET /api/v1/system/info

**获取系统信息**

（无请求参数）

- **出参**：GetSystemInfoResponse
- **鉴权**：Viewer；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### GET /api/v1/system/parser-engines

**列出可用的文档解析引擎**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### POST /api/v1/system/parser-engines/check

**使用当前参数检测解析引擎可用性**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| body | 解析引擎配置（与保存接口同结构） | body | object | 是 |

- **出参**：无
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### POST /api/v1/system/sandbox-check

**测试沙箱连通性**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| body | 沙箱配置 | body | SandboxCheckRequest | 是 |

- **出参**：SandboxCheckResponse
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### POST /api/v1/system/storage-engine-check

**测试存储引擎连通性**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| body | 存储引擎配置 | body | StorageCheckRequest | 是 |

- **出参**：StorageCheckResponse
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### GET /api/v1/system/storage-engine-status

**获取存储引擎状态**

（无请求参数）

- **出参**：GetStorageEngineStatusResponse
- **鉴权**：Viewer；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途；本节汇集所有无任何 tag 的基础设施端点）：**

- GET /api/v1/files/presigned — （公开；HMAC 签名 URL 自校验）
- HEAD /api/v1/files/presigned — （同上）
- GET /api/v1/files/presigned-preview — （Admin，显式拒绝 API Key）
- GET /api/v1/knowledge-bases/:id/files — （Viewer + KBAccessRead(id)；apiKeyRetrieve(apiKeyFullAccess())）
- GET /api/v1/local-browser/extension — （公开，注册在 Auth 中间件之前）
- POST /api/v1/local-browser/extension/authorize — （同上）
- POST /api/v1/local-browser/internal — （同上）
- GET /api/v1/me/browser — （需认证，无角色下限）
- POST /api/v1/me/browser — （同上）
- GET /api/v1/me/browser/extension — （同上）
- GET /api/v1/sessions/:id/messages/:message_id/files — （Viewer；apiKeyChat(apiKeyFullAccess())）
- GET /files — （需认证，无角色下限；仅 full-access/全租户 retrieve Key，KB 受限 Key 拒绝）
- GET /health — （公开）
- GET /r/:token — （公开，短时能力令牌自校验）
- HEAD /r/:token — （同上）
- GET /swagger/*any — （公开，仅非 release 模式启用）

### VectorStore

#### GET /api/v1/vector-stores

**List vector stores**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（env + DB 中的向量库列表）
- **鉴权**：Viewer；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### POST /api/v1/vector-stores

**Create vector store**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Vector store configuration | body | CreateStoreRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### POST /api/v1/vector-stores/test

**Test vector store connection with raw credentials**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Engine type and connection config | body | TestStoreRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（success, version）
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### GET /api/v1/vector-stores/types

**List vector store types**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### DELETE /api/v1/vector-stores/:id

**Delete vector store**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Vector store ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### GET /api/v1/vector-stores/:id

**Get vector store**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Vector store ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### PUT /api/v1/vector-stores/:id

**Update vector store**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Vector store ID | path | string | 是 |
| request | Updated fields | body | UpdateStoreRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

#### POST /api/v1/vector-stores/:id/test

**Test vector store connection by ID**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Vector store ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageVectorStores(apiKeyFullAccess())

### MCP端点

#### GET /api/v1/mcp-endpoints

**获取 MCP 端点列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### POST /api/v1/mcp-endpoints

**创建 MCP 端点**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 端点配置：name、description、enabled、knowledge_base_ids、tools 等 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（含一次性 token）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### GET /api/v1/mcp-endpoints/tools

**获取 MCP 端点工具目录**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### DELETE /api/v1/mcp-endpoints/:endpoint_id

**删除 MCP 端点**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| endpoint_id | 端点 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### GET /api/v1/mcp-endpoints/:endpoint_id

**获取 MCP 端点详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| endpoint_id | 端点 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### PUT /api/v1/mcp-endpoints/:endpoint_id

**更新 MCP 端点**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| endpoint_id | 端点 ID | path | string | 是 |
| request | 要更新的字段，未提供的字段保持不变 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### POST /api/v1/mcp-endpoints/:endpoint_id/rotate-token

**轮换 MCP 端点令牌**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| endpoint_id | 端点 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（含新 token 的端点）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

### Skills

#### GET /api/v1/skills

**获取当前沙箱配置上可执行的 Skills**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| sandbox_config_id | Sandbox config ID | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（skills 主组未接 apiKeyGroup）

#### GET /api/v1/skills/catalog

**List workspace skills**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（skills 主组未接 apiKeyGroup）

#### POST /api/v1/skills/catalog

**Add a skill to the workspace catalog**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：Viewer；API Key：未声明（skills 主组未接 apiKeyGroup）

#### DELETE /api/v1/skills/catalog/:id

**Delete a catalog skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Catalog skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyFullAccess

#### GET /api/v1/skills/catalog/:id/files

**List files of a catalog skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Catalog skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyFullAccess

#### GET /api/v1/skills/catalog/:id/files/content

**Read one file of a catalog skill**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Catalog skill ID | path | string | 是 |
| path | Skill-root-relative file path | query | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyFullAccess

#### POST /api/v1/skills/catalog/:id/install

**Install a catalog skill onto sandboxes**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Catalog skill ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Accepted）
- **鉴权**：Admin；API Key：apiKeyFullAccess

### 网络搜索

#### POST /api/v1/web-search-providers/test

**使用原始凭证测试 Provider（不落库）**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | {provider, parameters} | body | TestProviderRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（测试结果）
- **鉴权**：Admin；API Key：apiKeyManageWebSearch(apiKeyFullAccess())

#### GET /api/v1/web-search-providers/types

**获取网络搜索 Provider 类型元数据**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageWebSearch(apiKeyFullAccess())

#### DELETE /api/v1/web-search-providers/:id

**删除网络搜索 Provider**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Provider ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（success: true）
- **鉴权**：Admin；API Key：apiKeyManageWebSearch(apiKeyFullAccess())

#### GET /api/v1/web-search-providers/:id

**获取网络搜索 Provider 详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Provider ID | path | string | 是 |

- **出参**：WebSearchProviderEntity
- **鉴权**：Viewer；API Key：apiKeyManageWebSearch(apiKeyFullAccess())

#### PUT /api/v1/web-search-providers/:id

**更新网络搜索 Provider**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Provider ID | path | string | 是 |
| request | 更新字段 | body | UpdateProviderRequest | 是 |

- **出参**：WebSearchProviderEntity
- **鉴权**：Admin；API Key：apiKeyManageWebSearch(apiKeyFullAccess())

#### POST /api/v1/web-search-providers/:id/test

**测试已保存的 Provider**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | Provider ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Admin；API Key：apiKeyManageWebSearch(apiKeyFullAccess())

#### GET /api/v1/web-search/providers

**获取可用网络搜索 Provider 列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

**以下端点无接口注解（代码反推用途）：**

- GET /api/v1/web-search-providers — （鉴权 Viewer）
- POST /api/v1/web-search-providers — （鉴权 Admin）
- PUT /api/v1/web-search-providers/:id/credentials — （鉴权 Admin）
- DELETE /api/v1/web-search-providers/:id/credentials/:field — （鉴权 Admin）

### 分块管理

#### GET /api/v1/chunks/by-id/:id

**通过ID获取分块**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 分块ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（分块详情）
- **鉴权**：Viewer + KBAccessReadFromChunkIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/chunks/by-id/:id/questions

**删除生成的问题**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 分块ID | path | string | 是 |
| request | 问题ID | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedChunkKBOrAdminFromChunkID + KBAccessWriteFromChunkIDParam(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/chunks/:knowledge_id

**删除知识下所有分块**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| knowledge_id | 知识ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedChunkKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(knowledge_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/chunks/:knowledge_id

**获取知识分块列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| knowledge_id | 知识ID | path | string | 是 |
| page | 页码 | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）（分块列表）
- **鉴权**：Viewer + KBAccessReadFromKnowledgeIDParam(knowledge_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/chunks/:knowledge_id/:id

**删除分块**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| knowledge_id | 知识ID | path | string | 是 |
| id | 分块ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedChunkKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(knowledge_id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### PUT /api/v1/chunks/:knowledge_id/:id

**更新分块**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| knowledge_id | 知识ID | path | string | 是 |
| id | 分块ID | path | string | 是 |
| request | 更新请求 | body | UpdateChunkRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的分块）
- **鉴权**：OwnedChunkKBOrAdmin + KBAccessWriteFromKnowledgeIDParam(knowledge_id)；API Key：apiKeyIngest(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- POST /api/v1/chunks/:knowledge_id/:id/revert — （鉴权 OwnedChunkKBOrAdmin + KBAccessWriteFromKnowledgeIDParam）
- GET /api/v1/chunks/:knowledge_id/:id/revisions — （鉴权 Viewer + KBAccessReadFromKnowledgeIDParam）
- PUT /api/v1/chunks/by-id/:id/questions — （鉴权 OwnedChunkKBOrAdminFromChunkID + KBAccessWriteFromChunkIDParam）
- POST /api/v1/chunks/by-id/:id/questions/regenerate — （同上）

### 模型管理

#### GET /api/v1/models

**获取模型列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（模型列表）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/models

**创建模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 模型信息 | body | CreateModelRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的模型）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/models/providers

**获取模型厂商列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| model_type | 模型类型 (chat, embedding, rerank, vllm) | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### DELETE /api/v1/models/:id

**删除模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 模型ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

#### GET /api/v1/models/:id

**获取模型详情**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 模型ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### PUT /api/v1/models/:id

**更新模型**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 模型ID | path | string | 是 |
| request | 更新信息 | body | UpdateModelRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的模型）
- **鉴权**：AdminOrSystemAdmin；API Key：apiKeyManageModels(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途）：**

- PUT /api/v1/models/:id/credentials — （鉴权 AdminOrSystemAdmin）
- DELETE /api/v1/models/:id/credentials/:field — （鉴权 AdminOrSystemAdmin）
- POST /api/v1/models/:id/debug — （鉴权 Admin）

### IM 渠道

#### DELETE /api/v1/im-channels/:id

**删除 IM 渠道**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 渠道 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（success: true）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### PUT /api/v1/im-channels/:id

**更新 IM 渠道**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 渠道 ID | path | string | 是 |
| request | 更新字段（name/mode/output_mode/knowledge_base_id/credentials/enabled） | body | object（未

强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的渠道）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### POST /api/v1/im-channels/:id/toggle

**启用/停用 IM 渠道**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 渠道 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的渠道）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### POST /api/v1/wechat/qrcode

**获取微信扫码登录二维码**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（qrcode_url + qrcode 标识）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

#### POST /api/v1/wechat/qrcode/status

**轮询微信二维码状态**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | {qrcode: string} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（扫码状态）
- **鉴权**：Admin；API Key：apiKeyManageChannels(apiKeyFullAccess())

**以下端点无接口注解（代码反推用途；本节含全部 Embed 组件端点——见「注解与实现的差异」中关于 Embed 缺少独立 tag 的说明）：**

- GET /api/v1/agents/:id/embed-channels — （鉴权 Viewer）
- POST /api/v1/agents/:id/embed-channels — （鉴权 Admin）
- GET /api/v1/agents/:id/im-channels — （鉴权 Viewer）
- POST /api/v1/agents/:id/im-channels — （鉴权 Admin）
- GET /api/v1/embed-channels — （鉴权 Viewer）
- DELETE /api/v1/embed-channels/:channel_id — （鉴权 Admin）
- GET /api/v1/embed-channels/:channel_id — （鉴权 Viewer）
- PUT /api/v1/embed-channels/:channel_id — （鉴权 Admin）
- POST /api/v1/embed-channels/:channel_id/preview-session — （鉴权 Viewer）
- POST /api/v1/embed-channels/:channel_id/rotate-token — （鉴权 Admin）
- GET /api/v1/embed-channels/:channel_id/stats — （鉴权 Viewer）
- GET /api/v1/embed-frame-policy — （公开）
- POST /api/v1/embed/:channel_id/agent-chat/:session_id — （公开，独立 embed 频道令牌 EmbedAuth）
- GET /api/v1/embed/:channel_id/chunks/:chunk_id — （同上）
- GET /api/v1/embed/:channel_id/config — （同上）
- POST /api/v1/embed/:channel_id/exchange — （同上）
- GET /api/v1/embed/:channel_id/files — （同上）
- POST /api/v1/embed/:channel_id/knowledge-chat/:session_id — （同上）
- GET /api/v1/embed/:channel_id/messages/:session_id/load — （同上）
- POST /api/v1/embed/:channel_id/sessions — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/events — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/mcp-oauth-resolutions/:pending_id — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/mcp-oauth-resolutions/:pending_id/cancel — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/mcp-services/:id/oauth/authorize-url — （同上）
- GET /api/v1/embed/:channel_id/sessions/:session_id/mcp-services/:id/oauth/status — （同上）
- GET /api/v1/embed/:channel_id/sessions/:session_id/messages/:message_id/suggestions — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/messages/:message_id/suggestions — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/stop — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/suggestion-events — （同上）
- POST /api/v1/embed/:channel_id/sessions/:session_id/tool-approvals/:pending_id — （同上）
- GET /api/v1/embed/:channel_id/suggested-questions — （同上）
- GET /api/v1/im-channels — （鉴权 Viewer）

### 知识库共享

#### GET /api/v1/knowledge-bases/:id/shares

**获取知识库的共享列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |

- **出参**：ListSharesResponse
- **鉴权**：Viewer；API Key：apiKeyFullAccess

#### POST /api/v1/knowledge-bases/:id/shares

**共享知识库到组织**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 共享信息 | body | ShareKnowledgeBaseRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：OwnedKBOrAdmin；API Key：apiKeyFullAccess

#### DELETE /api/v1/knowledge-bases/:id/shares/:share_id

**取消共享**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| share_id | 共享记录ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：OwnedKBOrAdmin；API Key：apiKeyFullAccess

#### PUT /api/v1/knowledge-bases/:id/shares/:share_id

**更新共享权限**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| share_id | 共享记录ID | path | string | 是 |
| request | 权限信息 | body | UpdateSharePermissionRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：OwnedKBOrAdmin；API Key：apiKeyFullAccess

#### GET /api/v1/shared-knowledge-bases

**获取共享给我的知识库列表**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

### Me

#### GET /api/v1/me/env-vars

**List my environment variables**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（One group per sandbox config）
- **鉴权**：需认证，无角色下限（限定为调用者本人）；API Key：未声明

#### DELETE /api/v1/me/env-vars/sandbox

**Delete one of my sandbox environment variables**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Sandbox config and variable name | body | meEnvVarRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Deleted）
- **鉴权**：需认证，无角色下限（限定为调用者本人）；API Key：未声明

#### PUT /api/v1/me/env-vars/sandbox

**Set one of my sandbox environment variables**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Sandbox config, variable name and value | body | meEnvVarRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Stored）
- **鉴权**：需认证，无角色下限（限定为调用者本人）；API Key：未声明

#### DELETE /api/v1/me/env-vars/skill

**Delete one of my skill credentials**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Skill and variable name | body | meEnvVarRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Deleted）
- **鉴权**：需认证，无角色下限（限定为调用者本人）；API Key：未声明

#### PUT /api/v1/me/env-vars/skill

**Set one of my skill credentials**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | Skill, variable name and value | body | meEnvVarRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Stored）
- **鉴权**：需认证，无角色下限（限定为调用者本人）；API Key：未声明

### 我的邀请

#### GET /api/v1/me/invitations

**列出我的待接受邀请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| include_terminal | 是否包含已处理/已过期等终止态行（默认 false） | query | boolean | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：需认证，无角色下限（限定操作对象为调用者本人）；API Key：未声明

#### POST /api/v1/me/invitations/accept-by-token

**通过共享链接加入空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 邀请 token | body | acceptInvitationByTokenRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：需认证，无角色下限（限定操作对象为调用者本人）；API Key：未声明

#### GET /api/v1/me/invitations/pending-count

**获取我的待处理邀请数**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：需认证，无角色下限（限定操作对象为调用者本人）；API Key：未声明

#### POST /api/v1/me/invitations/:inv_id/accept

**接受邀请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| inv_id | 邀请 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：需认证，无角色下限（限定操作对象为调用者本人）；API Key：未声明

#### POST /api/v1/me/invitations/:inv_id/decline

**拒绝邀请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| inv_id | 邀请 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：需认证，无角色下限（限定操作对象为调用者本人）；API Key：未声明

### 空间成员

#### POST /api/v1/tenants/:id/leave

**退出当前空间**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：PathTenantMatch + Viewer；API Key：未声明

#### GET /api/v1/tenants/:id/members

**列出空间成员**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| q | 按邮箱/用户名模糊筛选 | query | string | 否 |
| page | 页码（从 1 起） | query | integer | 否 |
| page_size | 每页数量（最大 100） | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：PathTenantMatch + Viewer；API Key：apiKeyManageMembers(apiKeyFullAccess())

#### POST /api/v1/tenants/:id/members

**直接添加空间成员（直加路径）**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| request | 邀请请求 | body | addMemberRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyManageMembers(apiKeyFullAccess())

#### DELETE /api/v1/tenants/:id/members/:user_id

**移除空间成员**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| user_id | 用户 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyManageMembers(apiKeyFullAccess())

#### PUT /api/v1/tenants/:id/members/:user_id

**修改空间成员角色**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| user_id | 用户 ID | path | string | 是 |
| request | 目标角色 | body | updateMemberRoleRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyManageMembers(apiKeyFullAccess())

### 标签管理

#### GET /api/v1/knowledge-bases/:id/tags

**获取标签列表**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| page | 页码 | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |
| keyword | 关键词搜索 | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（标签列表）
- **鉴权**：Viewer + KBAccessRead(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### POST /api/v1/knowledge-bases/:id/tags

**创建标签**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| request | 标签信息 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（创建的标签）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

#### DELETE /api/v1/knowledge-bases/:id/tags/:tag_id

**删除标签**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| tag_id | 标签ID (UUID或seq_id) | path | string | 是 |
| force | 强制删除 | query | boolean | 否 |
| content_only | 仅删除内容，保留标签 | query | boolean | 否 |
| body | 删除选项 | body | DeleteTagRequest | 否 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())。**（待确认：query 参数 force/content_only 与 body DeleteTagRequest 双重表达删除选项，见待确认清单）**

#### PUT /api/v1/knowledge-bases/:id/tags/:tag_id

**更新标签**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 知识库ID | path | string | 是 |
| tag_id | 标签ID (UUID或seq_id) | path | string | 是 |
| request | 标签更新信息 | body | object | 是 |

- **出参**：object（未强类型，字段见 summary/description）（更新后的标签）
- **鉴权**：OwnedKBOrAdmin + KBAccessWrite(id)；API Key：apiKeyIngest(apiKeyFullAccess())

### 消息

#### GET /api/v1/messages/chat-history-stats

**获取聊天历史知识库统计**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：apiKeyFullAccess

#### POST /api/v1/messages/search

**搜索历史对话**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 搜索请求 | body | SearchMessagesRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（搜索结果）
- **鉴权**：Viewer；API Key：apiKeyFullAccess

#### GET /api/v1/messages/:session_id/load

**加载消息历史**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |
| limit | 返回数量 | query | integer | 否 |
| before_time | 在此时间之前的消息（RFC3339Nano格式） | query | string | 否 |
| resource_urls | 文件引用形式，public 返回可加载直链 | query | string | 否 |

- **出参**：object（未强类型，字段见 summary/description）（消息列表）
- **鉴权**：Viewer；API Key：apiKeyFullAccess

#### DELETE /api/v1/messages/:session_id/:id

**删除消息**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| session_id | 会话ID | path | string | 是 |
| id | 消息ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（删除成功）
- **鉴权**：Viewer；API Key：apiKeyFullAccess

### 空间邀请

#### GET /api/v1/tenants/:id/invitations

**列出空间邀请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| include_terminal | 是否包含终止态行（默认 false） | query | boolean | 否 |
| page | 页码（从 1 起） | query | integer | 否 |
| page_size | 每页数量 | query | integer | 否 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：PathTenantMatch + Viewer；API Key：apiKeyManageMembers(apiKeyFullAccess())

#### POST /api/v1/tenants/:id/invitations

**发出空间邀请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| request | 邀请请求 | body | createInvitationRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyManageMembers(apiKeyFullAccess())

#### DELETE /api/v1/tenants/:id/invitations/:inv_id

**撤销待接受邀请**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| inv_id | 邀请 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyManageMembers(apiKeyFullAccess())

#### POST /api/v1/tenants/:id/invite-links

**生成共享邀请链接**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间 ID | path | string | 是 |
| request | 共享链接配置 | body | createInviteLinkRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（Created）
- **鉴权**：PathTenantMatch + Owner；API Key：apiKeyManageMembers(apiKeyFullAccess())

### 组织

#### DELETE /api/v1/agents/:id/shares/:share_id

**取消智能体共享**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 智能体 ID | path | string | 是 |
| share_id | 共享记录 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（success: true）
- **鉴权**：OwnedAgentOrAdmin；API Key：apiKeyFullAccess

#### GET /api/v1/organizations/:id/agent-shares

**获取共享到本组织的智能体**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 组织 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（智能体共享列表 + total）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/shared-agents

**获取我可访问的共享智能体**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（智能体列表 + total）
- **鉴权**：Viewer；API Key：apiKeyManageSpaces(apiKeyFullAccess())

### 未分类

#### GET /api/v1/organizations/:id/search-users

**(无 summary)**

（无请求参数）

- **出参**：无 2xx 响应定义
- **鉴权**：Admin；API Key：apiKeyManageSpaces(apiKeyFullAccess())

#### GET /api/v1/sessions/:session_id/messages/:message_id/artifacts

**(无 summary)**

（无请求参数）

- **出参**：无 2xx 响应定义
- **鉴权**：Viewer（挂在 sessions 分组级别）；API Key：apiKeyChat(apiKeyFullAccess())

#### GET /api/v1/sessions/:session_id/messages/:message_id/artifacts/:index/download

**(无 summary)**

（无请求参数）

- **出参**：无 2xx 响应定义
- **鉴权**：Viewer（挂在 sessions 分组级别）；API Key：apiKeyChat(apiKeyFullAccess())

### User

#### GET /api/v1/user/favorites

**List my favorites**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| type | Resource type (kb \| agent) | query | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

#### POST /api/v1/user/favorites

**Star a resource**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| body | Type + id | body | AddFavoriteRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

#### DELETE /api/v1/user/favorites/:type/:id

**Unstar a resource**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| type | Resource type | path | string | 是 |
| id | Resource id | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）
- **鉴权**：Viewer；API Key：未声明（不可通过 API Key 调用）

### 评估

#### GET /api/v1/evaluation/

**获取评估结果**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| task_id | 评估任务ID | query | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（评估结果）
- **鉴权**：Viewer；API Key：apiKeyRunEvaluations(apiKeyFullAccess())。**注**：真实路径无尾部斜杠（`GET /api/v1/evaluation`），swagger 注解多写了一个 `/`，gin 会自动规整匹配，非真实缺陷（见「注解与实现的差异」）。

#### POST /api/v1/evaluation/

**执行评估**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | 评估请求参数 | body | EvaluationRequest | 是 |

- **出参**：object（未强类型，字段见 summary/description）（评估任务）
- **鉴权**：Admin；API Key：apiKeyRunEvaluations(apiKeyFullAccess())。**注**：同上，真实路径无尾部斜杠。

### IM 回调

#### GET /api/v1/im/callback/:channel_id

**IM 平台回调**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| channel_id | 渠道 ID | path | string | 是 |

- **出参**：object（未强类型，字段见 summary/description）（处理结果）
- **鉴权**：公开（IM 平台回调 webhook）；API Key：不适用

#### POST /api/v1/im/callback/:channel_id

**IM 平台回调**

（参数同上）

- **出参**：object（未强类型，字段见 summary/description）（处理结果）
- **鉴权**：公开（IM 平台回调 webhook）；API Key：不适用

### 知识

#### POST /api/v1/knowledge/move

**移动知识到其他知识库**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | {source_kb_id, target_kb_id, knowledge_ids} | body | MoveKnowledgeRequest | 是 |

- **出参**：MoveKnowledgeResponse（任务信息）
- **鉴权**：Contributor（批量操作跨多个 KB，不做单 KB KBAccess 校验）；API Key：apiKeyIngest(apiKeyFullAccess())

#### GET /api/v1/knowledge/move/progress/:task_id

**获取知识移动进度**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| task_id | 移动任务 ID | path | string | 是 |

- **出参**：KnowledgeMoveProgress
- **鉴权**：Viewer；API Key：apiKeyIngest(apiKeyFullAccess())

### WeKnoraCloud

#### GET /api/v1/models/weknoracloud/status

**检查 WeKnoraCloud 凭证状态**

（无请求参数）

- **出参**：object（未强类型，字段见 summary/description）（凭证状态）
- **鉴权**：Viewer；API Key：apiKeyManageModels(apiKeyFullAccess())

#### POST /api/v1/weknoracloud/credentials

**保存 WeKnoraCloud 凭证**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | {app_id, app_secret} | body | object（未强类型） | 是 |

- **出参**：object（未强类型，字段见 summary/description）（success: true）
- **鉴权**：Admin；API Key：apiKeyManageModels(apiKeyFullAccess())

### 审计日志

#### GET /api/v1/system/admin/audit-log

**获取平台审计日志**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| after_id | 游标：返回 id 小于此值的记录（默认从最新开始） | query | integer | 否 |
| limit | 页大小，1-100，默认 50 | query | integer | 否 |
| action | 按 action 精确过滤（如 system.setting_changed） | query | string | 否 |
| outcome | 按 outcome 精确过滤（success / denied） | query | string | 否 |
| actor | 按 actor_user_id 精确过滤 | query | string | 否 |

- **出参**：auditLogListResponse
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_audit_read)

#### GET /api/v1/tenants/:id/audit-log

**获取空间审计日志**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| id | 空间ID | path | string | 是 |
| after_id | 游标：返回 id 小于此值的记录（默认从最新开始） | query | integer | 否 |
| limit | 页大小，1-100，默认 50 | query | integer | 否 |
| action | 按 action 精确过滤（如 rbac.member_added / rbac.access_denied） | query | string | 否 |
| outcome | 按 outcome 精确过滤（success / denied） | query | string | 否 |
| actor | 按 actor_user_id 精确过滤 | query | string | 否 |

- **出参**：auditLogListResponse
- **鉴权**：PathTenantMatch + Admin；API Key：未声明

### 分块

#### POST /api/v1/chunker/preview

**预览分块结果**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| request | {text, chunking_config} | body | PreviewChunkingRequest | 是 |

- **出参**：PreviewChunkingResponse（分块结果）
- **鉴权**：Viewer；API Key：apiKeyRetrieve(apiKeyIngest(apiKeyFullAccess()))

### Knowledge

#### GET /api/v1/knowledge/search

**Search knowledge**

| 参数名 | 说明 | 位置 | 类型 | 必填 |
|---|---|---|---|---|
| keyword | Keyword to search | query | string | 否 |
| offset | Offset for pagination (minimum 0) | query | integer | 否 |
| limit | Limit for pagination (default 20, maximum 100) | query | integer | 否 |
| file_types | Comma-separated file extensions to filter (e.g., csv,xlsx) | query | string | 否 |
| agent_id | Shared agent ID (search within agent's KB scope) | query | string | 否 |
| recent | Return recent files when keyword is empty | query | boolean | 否 |

- **出参**：object（未强类型，字段见 summary/description）（Search results）
- **鉴权**：Viewer；API Key：apiKeyIngest(apiKeyFullAccess())

### 系统管理

#### GET /api/v1/system/admin/runtime/queues

**获取解析任务队列运行时状态**

（无请求参数）

- **出参**：RuntimeQueuesResponse
- **鉴权**：SystemAdmin；API Key：apiKeyPlatform(system_runtime_read, system_runtime_manage)

---

## 注解与实现的差异

### swagger 有但代码路由没有的条目（原始比对命中 16 条，逐条核实归因）

**A. 真实缺陷——文档路径与实现不符**（3 条）

1. `GET /api/v1/api/v1/knowledge/{id}/spans` — `@Router` 把 basePath 写重了一次。注解位置 `internal/handler/knowledge.go:602`。真实路由是 `GET /api/v1/knowledge/:id/spans`（`internal/router/routes_knowledge.go` `RegisterKnowledgeRoutes`，与 `/stages` 共用 handler `GetKnowledgeSpans`）。
2. `GET /api/v1/mcp-services/oauth/callback` — 文档把回调路径挂在 `/mcp-services` 子组下，但代码里 `RegisterMCPServiceRoutes`（`internal/router/routes_infra.go`）把它直接注册在 v1 根组，真实路径是 `GET /api/v1/mcp-oauth/callback`。注解位置 `internal/handler/mcp_oauth.go:136`。
3. `POST /api/v1/sessions/{session_id}/title` — 文档路径漏了 `/generate_title` 后缀，真实路径是 `POST /api/v1/sessions/:session_id/generate_title`（`internal/router/routes_chat.go` `RegisterSessionRoutes`）。注解位置 `internal/handler/session/title.go:24`。

**B. 内部分发函数误加重复注解（幽灵端点）**（2 条）

4. `GET /api/v1/tenants/kv/prompt-templates`
5. `GET /api/v1/tenants/kv/web-search-config`
   — 真实只有一个通用路由 `GET /api/v1/tenants/kv/:key`（`internal/router/routes_auth_tenant.go` `RegisterTenantRoutes`），由 `TenantHandler.GetTenantKV`（`internal/handler/tenant.go:1304`）按 `key` 值内部分发到 `GetPromptTemplates`（`:1605`）、`GetTenantWebSearchConfig`（`:1453`）等子函数；这两个子函数各自额外写了一份 `@Router` 注解，把某个具体 key 值误当成了独立端点。建议删除这两条注解，只保留外层 `GetTenantKV` 的通用注解。

**C. 通配符 vs 路径参数语义不一致（待确认，非纯粹路由缺失）**（4 条）

6. `DELETE /api/v1/knowledgebase/{kb_id}/wiki/pages/{slug}`
7. `GET /api/v1/knowledgebase/{kb_id}/wiki/pages/{slug}`
8. `PUT /api/v1/knowledgebase/{kb_id}/wiki/pages/{slug}`
9. `GET /api/v1/knowledgebase/{kb_id}/wiki/revisions/{slug}`
   — swagger 声明 `{slug}` 为普通单段路径参数，但实现（`internal/router/routes_knowledge.go` `RegisterWikiPageRoutes`）用的是 gin 通配符 `*slug`（如 `wikiRead.GET("/pages/*slug", ...)`），会匹配含 `/` 的整段路径，语义比文档描述的更宽。**（待确认：动词/参数语义不符）**

**D. 参数命名不一致（doc 用 `session_id`，实现用 `id`；语义相同，非缺陷）**（4 条）

10. `GET /api/v1/sessions/{session_id}/artifacts`（实现 `:id`）
11. `GET /api/v1/sessions/{session_id}/messages/{message_id}/artifacts`（实现 `:id`，且此条无 summary）
12. `GET /api/v1/sessions/{session_id}/messages/{message_id}/artifacts/{index}/download`（实现 `:id`，无 summary）
13. `GET /api/v1/sessions/{session_id}/messages/{message_id}/suggestions`（实现 `:id`）

**E. 尾部斜杠（gin 对 group-root 会 `TrimRight` 规整，非真实问题）**（2 条）

14. `GET /api/v1/evaluation/`
15. `POST /api/v1/evaluation/`

**已排除的假阳性**（1 条）：`GET /knowledge-bases/copy/progress/{task_id}` 最初对账也会显示为"代码没有"，但核实后路由确实存在（`internal/router/routes_knowledge.go:246-247`：`kb.With(apiKeyRetrieve(apiKeyManageKnowledgeBases(apiKeyFullAccess()))).\n\tGET("/copy/progress/:task_id", ...)`），只是这个跨行的 `.With(...).GET(...)` 链式写法未被中间产物 `api_routes.json` 的提取脚本 `extract_routes.py` 的正则捕获——**该中间产物存在提取盲点，462 应为 463**。

### 代码有但 swagger 未覆盖的 92 个（按模块归类）

| 模块 | 数量 | 代表性端点 |
|---|---|---|
| IM 渠道（含全部 Embed 组件） | 32 | `POST /embed-channels`(创建)、`POST /embed/:channel_id/sessions`(创建 embed 会话)、`GET /im-channels` |
| 会话 | 13 | `POST/GET/DELETE /sessions/:id/attachments*`(临时附件全套)、`POST /sessions/:session_id/sandbox/{terminal,desktop}-ticket`、`GET /sessions/:id/sandbox/{terminal,desktop}`(WS) |
| routes_infra.go 系（DataSource/模型管理/网络搜索/MCP服务/SandboxConfig 的凭证与子资源） | 15 | `PUT/DELETE /datasource/:id/credentials*`、`PUT/DELETE /models/:id/credentials*`、`GET/POST /web-search-providers`(列表/创建，而 update/delete 反而有文档)、`GET /mcp-services/:id/tool-approvals`、`GET/POST /sandbox-configs/:id/skills/:skillId/guidance` |
| 系统（无 tag 的文件服务与基础设施） | 16 | `GET /files`、`GET/HEAD /r/:token`、`GET/HEAD /files/presigned(-preview)`、`GET /knowledge-bases/:id/files`、`GET /health`、`GET /swagger/*any`、`GET/POST /local-browser/*`、`GET/POST /me/browser*` |
| 知识管理/知识库/分块管理 | 8 | `GET /knowledge/:id/{stages,spans}`、`POST /knowledge/:id/regenerate-summary`、`POST /knowledge-bases/:id/profile/generate`、`GET /chunks/:knowledge_id/:id/revisions`、`POST .../revert`、`PUT/POST .../questions*` |
| 空间管理 / System Admin | 5 | `GET/POST /tenants/:id/api-keys`、`PUT/DELETE /tenants/:id/api-keys/:key_id`、`GET /system/admin/settings` |
| 组织管理 | 3 | `GET/POST /agents/:id/shares`、`POST /shared-agents/disabled` |

合计 32+13+15+16+8+5+3 = 92，与逐模块小节末尾列出的清单一一对应（一条不漏）。其中最突出的两个覆盖空白：**Embed 嵌入式组件**（频道管理 8 个 + 公开消费端 23 个，共 31 个，占 92 个未覆盖端点的三分之一）和**文件服务基础设施**（8 个）在 43 个 tag 里都没有对应的独立分类，被本报告分别并入"IM 渠道"和"系统"仅为方便定位，不代表原始设计意图。

---

## 待确认清单

- [ ] `组织` 与 `组织管理` 两个 tag 语义重叠，建议合并（见 `GET/POST /agents/:id/shares`、`POST /shared-agents/disabled` 等被归入"组织管理"小节末尾的未注解端点）
- [ ] `知识` 与 `知识管理` 两个 tag 重叠（见 `POST /knowledge/move`、`GET /knowledge/move/progress/:task_id`）
- [ ] `Knowledge`（英文）与 `知识管理`（中文）重叠（见 `GET /knowledge/search`）
- [ ] `分块` 与 `分块管理` 重叠（见 `POST /chunker/preview`）
- [ ] `系统管理`（中文）与 `System Admin`（英文）重叠（见 `GET /system/admin/runtime/queues`）
- [ ] `GET /api/v1/knowledge/{id}/spans` 的 `@Router` 注解 basePath 写重，需修复为 `/knowledge/{id}/spans`（`internal/handler/knowledge.go:602`）
- [ ] `GET /knowledge/:id/stages` 与 `/spans` 共用同一 handler 却完全没有独立注解，建议至少给 stages 补一条
- [ ] `GET /mcp-services/oauth/callback` 文档路径与实现路径 `/mcp-oauth/callback` 不一致（`internal/handler/mcp_oauth.go:136`）
- [ ] `POST /sessions/{session_id}/title` 文档路径与实现路径 `.../generate_title` 不一致（`internal/handler/session/title.go:24`）
- [ ] `GET /tenants/kv/prompt-templates`、`GET /tenants/kv/web-search-config` 是内部分发函数误加的重复注解，建议删除，只保留通用的 `GET /tenants/kv/{key}`（`internal/handler/tenant.go:1452,1604`）
- [ ] Wiki 的 `pages/{slug}`、`revisions/{slug}` 用 gin 通配符 `*slug` 实现但文档写成普通路径参数 `{slug}`，slug 含 `/` 时的匹配行为可能超出前端预期，需要澄清 **（待确认：动词与语义不符）**
- [ ] Embed（嵌入式组件）整个功能域（约 31 个端点：频道管理 + 公开消费端）在 swagger 43 个 tag 里完全没有出现，建议新增独立 `Embed` tag
- [ ] 文件服务基础设施（`/files`、`/r/:token`、`/files/presigned(-preview)`、KB/消息 scoped 文件代理，共 8 个）无 tag 覆盖，建议新增 `Files` tag
- [ ] 中间产物 `api_routes.json` 存在提取盲点：`GET /knowledge-bases/copy/progress/:task_id` 因 `.With(...).\nGET(...)` 跨行链式调用未被 `extract_routes.py` 正则捕获，实际路由总数应为 463 而非 462（`internal/router/routes_knowledge.go:246-247`）
- [ ] `POST /knowledge-bases`（创建知识库）的 API Key 组默认能力位是 `apiKeyRetrieve`，创建操作本身并未额外要求 `apiKeyManageKnowledgeBases`，是否符合预期需与安全团队确认
- [ ] `GET/POST /web-search-providers`（列表/创建）没有 swagger 注解，但 update/delete/test 都有——覆盖不对称，需确认是遗漏还是刻意
- [ ] `GET/POST /sandbox-configs/:id/skills/:skillId/guidance` 两个同名端点动词含义需要核实（GET 获取安装指引 vs POST 语义不明）**（待确认：动词与语义不符）**
- [ ] `DELETE /knowledge-bases/:id/tags/:tag_id` 同时支持 query 参数 `force`/`content_only` 和 body `DeleteTagRequest` 表达删除选项，两套输入语义是否会冲突需要确认
- [ ] `agents` 资源组的 API Key 组默认能力位是裸 `apiKeyFullAccess`（未叠加 `manage_agents`），意味着任何 full-access Key 即可管理智能体，而 `sandbox-configs`/`memory` 等组也是同样模式——是否应统一补充细分能力位需产品/安全确认

---

## 候选领域信号

**候选领域实体**（从 DTO 类型名与资源路径反推）：`KnowledgeBase`、`Knowledge`（知识文档）、`Chunk`（分块）、`FAQEntry`/`Tag`、`WikiPage`/`WikiFolder`/`WikiPageIssue`/`WikiPageRevision`、`CustomAgent`、`Session`/`Message`/`Artifact`/临时附件(`TemporaryDocument`)、`MemoryItem`/`MemoryTopic`/记忆亲和文档、`Tenant`(空间)/`TenantMember`/`TenantInvitation`/`TenantAPIKey`、`Organization`/`KBShare`/`AgentShare`、`Model`/`VectorStore`/`StorageBackend`/`WebSearchProvider`/`DataSource`/`SyncLog`、`MCPService`/`MCPEndpoint`、`EmbedChannel`/`IMChannel`、评估任务、`AuditLog`、`SystemSetting`、`SandboxConfig`/Skill(Catalog)、用户收藏(`UserResourceFavorite`)、WeKnoraCloud 凭证。

**候选业务动作**（verb+resource 模式归纳）：
- **知识生命周期**：创建(file/url/manual) → 解析(reparse/cancel-parse) → 摘要(regenerate-summary) → 移动(move/folder) → 批量删除
- **知识库生命周期**：创建 → 初始化(initialize) → 配置(config) → 复制/克隆(copy/duplicate) → 迁移(move-targets) → 共享(share) → 置顶(pin) → 删除
- **会话生命周期**：创建 → 提问(knowledge-chat/agent-chat) → 转向(steer/inject) → 停止(stop) → 分叉(fork) → 置顶/归档/删除
- **Wiki 生命周期**：创建页面 → 版本(revision) → 回退(revert) → 质量检查(lint/issue) → 自动修复(auto-fix) → 重建链接(rebuild-links)
- **成员/邀请生命周期**：邀请(invite) → 接受/拒绝(accept/decline) → 角色变更 → 移除 → 离开(leave)
- **凭证子域**（跨 Model/DataSource/MCPService/WebSearchProvider/WeKnoraCloud 反复出现的统一模式）：保存(PUT credentials) → 按字段删除(DELETE credentials/:field) → 测试(POST test)，可提炼为通用"凭证管理"聚合根
- **MCP OAuth 生命周期**：发起(authorize-url) → 回调(callback) → 查询状态(status) → 撤销(revoke token)
- **审批(Approval)生命周期**（跨工具调用与 OAuth 两种资源出现相似模式）：待定 → 批准/拒绝 → 跳过(cancel)

以上信息基于对 `docs/swagger.json`（374 operations）、`internal/router/*.go`（全部 9 个注册 HTTP 路由的文件）、`internal/handler/*.go` 的 swaggo 注解块及 `internal/middleware/{auth,error_handler}.go`、`internal/errors/errors.go`、`internal/handler/list_pagination.go`、`internal/types/tenant_api_key.go` 的直接源码阅读整理，未臆造任何路径、参数名或字段。
