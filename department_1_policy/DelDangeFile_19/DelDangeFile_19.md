# 删除.netrc,.rhosts的文件

## 基本信息

| 字段 | 值 |
|------|-----|
| 加固项 | `DelDangeFile_19` |
| 部门 | `1` |
| 编号 | `19` |
| 状态键 | `119` |

## 配置说明

配置文件：`DelDangeFile_19.yaml`

- 描述：删除.netrc,.rhosts的文件
- 策略类：`DelDangeFile_19`

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

