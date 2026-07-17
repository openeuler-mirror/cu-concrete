# 为/usr/bin/containerd配置审计功能

## 基本信息

| 字段 | 值 |
|------|-----|
| 加固项 | `AuditUsContainerd_12` |
| 部门 | `2` |
| 编号 | `12` |
| 状态键 | `212` |

## 配置说明

配置文件：`AuditUsContainerd_12.yaml`

- 描述：为/usr/bin/containerd配置审计功能
- 策略类：`AuditUsContainerd_12`

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

