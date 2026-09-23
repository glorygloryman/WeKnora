## 表：web_search_providers

> 业务含义：租户配置的联网搜索服务商实例（Bing/Google/Tavily/Bocha等），供Agent联网检索使用
> 来源：000030_web_search_providers.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；NOT NULL | 配置ID |
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID |
| `name` | VARCHAR(255) | NOT NULL | 配置名称（如“生产环境Bing”） |
| `provider` | VARCHAR(50) | NOT NULL | 服务商类型：brave/bing/google/duckduckgo/tavily/ollama/baidu/searxng/keenable/zhipu/exa/metaso/bocha/serply |
| `description` | TEXT | — | 描述 |
| `parameters` | JSONB | — | 服务商参数（加密存储的API Key、Google引擎ID、自建实例BaseURL、代理URL、扩展配置等） |
| `is_default` | BOOLEAN | 默认 false | 是否为该工作空间的默认联网搜索提供商 |
| `created_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |
| `deleted_at` | TIMESTAMP | — | 审计字段：软删除时间 |

**索引**：
- `idx_web_search_providers_tenant_id` (`tenant_id`)
- `idx_web_search_providers_provider` (`provider`)
- `idx_web_search_providers_deleted_at` (`deleted_at`)

