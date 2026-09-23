## 表：mcp_metadata

> 业务含义：MCP服务的工具/资源目录快照缓存：按(服务,调用主体)显式同步的完整工具列表，供Agent发现工具而无需每次实时连接MCP服务器
> 类型：基础设施表，非业务表
> 来源：000092_mcp_metadata.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `tenant_id` | BIGINT | NOT NULL | 所属租户ID（联合主键） |
| `service_id` | VARCHAR(36) | NOT NULL；FK→mcp_services.id ON DELETE CASCADE | 所属MCP服务ID（联合主键） |
| `principal` | VARCHAR(255) | NOT NULL；默认 '' | 调用主体标识（OAuth场景下目录按授权主体隔离，联合主键） |
| `config_fingerprint` | VARCHAR(64) | NOT NULL | MCP服务连接配置指纹，用于判断配置变更导致目录需要重新同步 |
| `tools` | JSONB | NOT NULL | 同步到的工具列表（名称/描述/入参schema/是否需要审批） |
| `instructions` | TEXT | NOT NULL；默认 '' | MCP服务返回的整体使用说明 |
| `server_name` | TEXT | NOT NULL；默认 '' | MCP服务端上报的服务名 |
| `server_version` | TEXT | NOT NULL；默认 '' | MCP服务端上报的版本号 |
| `server_description` | TEXT | NOT NULL；默认 '' | MCP服务端上报的描述 |
| `synced_at` | TIMESTAMPTZ | NOT NULL | 最近一次同步时间 |

**外键**：
- `service_id` → mcp_services.id ON DELETE CASCADE

