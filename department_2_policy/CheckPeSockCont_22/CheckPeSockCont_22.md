# 修改containerd.sock文件权限

## 基本信息

| 字段 | 值 |
|------|-----|
| 加固项 | `CheckPeSockCont_22` |
| 部门 | `2` |
| 编号 | `22` |
| 状态键 | `222` |

## 配置说明

配置文件：`CheckPeSockCont_22.yaml`

- 描述：修改containerd.sock文件权限
- 策略类：`CheckPeSockCont_22`

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

