# 为containerd.toml配置审计功能

## 基本信息

| 字段 | 值 |
|------|-----|
| 加固项 | `AuditConToml_10` |
| 部门 | `2` |
| 编号 | `10` |
| 状态键 | `210` |

## 配置说明

配置文件：`AuditConToml_10.yaml`

- 描述：为containerd.toml配置审计功能
- 策略类：`AuditConToml_10`

## 方法说明

- `check()`：合规检查
- `fix()`：执行加固
- `rollback()`：回滚变更
- `reset()`：重置状态
- `get_des()`：读取描述

## 维护记录

- 优化日志输出与变量命名
- 加固状态写入前刷新 pkl 缓存
- 部门 `2` 策略持续迭代中

