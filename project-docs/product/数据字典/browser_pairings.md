## 表：browser_pairings

> 业务含义：浏览器扩展一次性配对令牌表：用户首次授权浏览器插件时的短时配对凭证，兑换成功后即删除
> 类型：基础设施表，非业务表
> 来源：000093_browser_authorization.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `scope_key` | VARCHAR(32) | PRIMARY KEY | 按(租户,用户)计算的作用域键，主键 |
| `token_hash` | VARCHAR(64) | NOT NULL；UNIQUE | 一次性配对令牌哈希 |
| `tenant` | BIGINT | NOT NULL | 所属租户ID |
| `user` | VARCHAR(36) | NOT NULL | 所属用户ID |
| `expires_at` | TIMESTAMPTZ | NOT NULL | 配对令牌过期时间（约5分钟） |

**索引**：
- `browser_pairings_expiry` (`expires_at`)

