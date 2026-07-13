# 禁止匿名账户登录ftp

## 基本信息

| 字段 | 值 |
|------|-----|
| 加固项 | `DisableFtpAnonymous_21` |
| 部门 | `1` |
| 编号 | `21` |
| 状态键 | `121` |

## 配置说明

配置文件：`DisableFtpAnonymous_21.yaml`

- 描述：禁止匿名账户登录ftp
- 策略类：`DisableFtpAnonymous_21`

## 方法说明

- `check()`：合规检查
- `fix()`：执行加固
- `rollback()`：回滚变更
- `reset()`：重置状态
- `get_des()`：读取描述

## 维护记录

- 优化日志输出与变量命名
- 加固状态写入前刷新 pkl 缓存
- 部门 `1` 策略持续迭代中

