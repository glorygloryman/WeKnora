## 表：browser_task_interruptions

> 业务含义：标记因浏览器连接中断而需要显式恢复的会话，供重新连接后续跑被打断的浏览器操作任务
> 类型：基础设施表，非业务表
> 来源：000093_browser_authorization.up.sql

| 字段 | 类型 | 约束 / 默认 | 含义 |
|---|---|---|---|
| `scope_key` | VARCHAR(32) | NOT NULL | 按(租户,用户)计算的作用域键 |
| `session` | VARCHAR(36) | NOT NULL | 被中断的会话ID |

