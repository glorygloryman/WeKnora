## 表：custom_agents

> 业务含义：自定义/内置智能体（Agent）定义：问答模式、系统提示词、工具/知识库范围、检索策略等全套运行配置
> 来源：000006_custom_agents.up.sql, 000043_tenant_rbac.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | NOT NULL；默认 uuid_generate_v4() | Agent ID（内置Agent为固定字符串如builtin-quick-answer，自定义Agent为UUID） |
| `name` | VARCHAR(255) | NOT NULL | Agent名称 |
| `description` | TEXT | — | Agent描述 |
| `avatar` | VARCHAR(64) | — | Agent头像（emoji或图标名） |
| `is_builtin` | BOOLEAN | NOT NULL；默认 false | 是否为内置Agent（普通模式/Agent模式基础款） |
| `tenant_id` | INTEGER | NOT NULL | 所属租户ID（与id组成联合主键） |
| `created_by` | VARCHAR(36) | — | 创建者用户ID |
| `config` | JSONB | NOT NULL；默认 '{}' | Agent完整运行配置（JSON）：模式(quick-answer快速问答/smart-reasoning推理智能体)、预设类型(rag-qa/wiki-qa/hybrid-rag-wiki/data-analysis/custom)、系统提示词、模型/重排模型、MCP与技能选择模式、沙箱配置、知识库选择、FAQ策略、联网搜索、多轮记忆、检索阈值、追问建议等 |
| `runnable_by_viewer` | BOOLEAN | NOT NULL；默认 TRUE | 是否允许仅有Viewer只读权限的用户运行该Agent |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | — | 审计字段：软删除时间 |

**索引**：
- `idx_custom_agents_tenant_id` (`tenant_id`)
- `idx_custom_agents_is_builtin` (`is_builtin`)
- `idx_custom_agents_deleted_at` (`deleted_at`)

