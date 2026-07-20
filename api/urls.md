# URL 路由说明

`urlpatterns` 将 REST path 绑定到 `views`：

- `execute-playbook/`、`tasks/`、`task-detail/`、`task-logs/`
- `pool-list/`、`pool-hosts/`、`harden-items/`
- `generate-config/`、`from-pool-get-configs/`、`save-conf-content/` 等

完整列表以 `urls.py` 为准。


---

## 摘录：平台接口文档（开头）

# cu-concrete 接口文档

本文档描述了 cu-concrete 安全合规检查与加固平台的所有 API 接口。

- **版本**：v1.0
- **日期**：2026-03-16
- **Base URL**：`http://127.0.0.1:8000`

---

## 目录

1. [云池管理](#1-云池管理)
2. [任务执行](#2-任务执行)
3. [任务查询](#3-任务查询)
4. [结果查询](#4-结果查询)
5. [附录](#附录)

---

## 分页规范

所有分页接口统一使用以下参数：

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| current | int | 否 | 当前页码，从1开始，默认1 |
| pageSize | int | 否 | 每页大小，默认10 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| count | int | 总条数 |
| pageIndex | int | 当前页码 |
| pageSize | int | 每页大小 |
| list | array | 数据列表 |

---

## 1. 云池管理

### 1.1 获取云池列表

**接口信息**

