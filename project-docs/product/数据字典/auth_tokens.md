## 表：auth_tokens

> 业务含义：用户身份令牌表：JWT等access/refresh token的持久化与吊销状态
> 来源：000001_agent.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY；默认 uuid_generate_v4() | Unique identifier of the token |
| `user_id` | VARCHAR(36) | NOT NULL | User ID that owns this token |
| `token` | TEXT | NOT NULL | Token value (JWT or other format) |
| `token_type` | VARCHAR(50) | NOT NULL | Token type (access_token, refresh_token) |
| `expires_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Token expiration time |
| `is_revoked` | BOOLEAN | NOT NULL；默认 false | Whether the token is revoked |
| `created_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：创建时间 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | 默认 CURRENT_TIMESTAMP | 审计字段：更新时间 |

**索引**：
- `idx_auth_tokens_user_id` (`user_id`)
- `idx_auth_tokens_token` (`token`)
- `idx_auth_tokens_token_type` (`token_type`)
- `idx_auth_tokens_expires_at` (`expires_at`)

**外键**：
- ADD CONSTRAINT fk_auth_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

