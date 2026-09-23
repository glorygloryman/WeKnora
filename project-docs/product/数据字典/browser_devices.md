## 表：browser_devices

> 业务含义：浏览器扩展远程控制配对成功后的长期设备凭证表：每个租户/用户当前仅保留一个已注册设备，供Agent通过Chrome插件操作用户本地浏览器
> 类型：基础设施表，非业务表
> 来源：000093_browser_authorization.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `scope_key` | VARCHAR(32) | PRIMARY KEY | 按(租户,用户)计算的作用域键，主键 |
| `id` | VARCHAR(32) | NOT NULL；UNIQUE | 设备ID |
| `tenant` | BIGINT | NOT NULL | 所属租户ID |
| `user` | VARCHAR(36) | NOT NULL | 所属用户ID |
| `label` | VARCHAR(100) | NOT NULL | 设备展示名称 |
| `token_hash` | VARCHAR(64) | NOT NULL；UNIQUE | 当前有效令牌的哈希 |
| `previous_hash` | VARCHAR(64) | NOT NULL；默认 '' | 轮换前旧令牌的哈希（宽限期内仍可用） |
| `previous_until` | TIMESTAMPTZ | NOT NULL | 旧令牌宽限期截止时间 |
| `expires_at` | TIMESTAMPTZ | NOT NULL | 设备凭证过期时间 |
| `renew_after` | TIMESTAMPTZ | NOT NULL | 达到该时间后建议续期 |
| `last_seen_at` | TIMESTAMPTZ | NOT NULL | 设备最近一次活跃时间 |
| `revoked_at` | TIMESTAMPTZ | — | 吊销时间 |
| `owner` | VARCHAR(32) | NOT NULL；默认 '' | 当前持有该设备连接的服务实例标识（用于多实例部署下的连接归属） |
| `owner_url` | VARCHAR(500) | NOT NULL；默认 '' | 当前持有连接的服务实例地址 |
| `lease_key` | VARCHAR(32) | NOT NULL；默认 '' | 连接租约键 |
| `lease_until` | TIMESTAMPTZ | NOT NULL | 连接租约到期时间，超时后其他实例可接管连接 |
| `created_at` | TIMESTAMPTZ | NOT NULL | 审计字段：创建时间 |

