# 为/etc/sysconfig/docker配置审计功能

## 基本信息

| 字段 | 值 |
|------|-----|
| 加固项 | `AuditSysconfig_11` |
| 部门 | `2` |
| 编号 | `11` |
| 状态键 | `211` |

## 配置说明

配置文件：`AuditSysconfig_11.yaml`

- 描述：为/etc/sysconfig/docker配置审计功能
- 策略类：`AuditSysconfig_11`

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

