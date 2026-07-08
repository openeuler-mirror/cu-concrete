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

| 属性 | 值 |
|------|-----|
| 接口地址 | `/cu-concrete/pool-list/` |
| 请求方法 | GET |
| Content-Type | application/json |
| 功能描述 | 获取所有可用的云池列表 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| current | int | 否 | 当前页码，默认1 |
| pageSize | int | 否 | 每页大小，默认全部 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，200表示成功 |
| message | string | 响应消息 |
| data.count | int | 总记录数 |
| data.pageIndex | int | 当前页码 |
| data.pageSize | int | 每页大小 |
| data.list[].id | string | 云池ID |
| data.list[].name | string | 云池名称 |

**成功响应示例（200）**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "count": 3,
    "pageIndex": 1,
    "pageSize": 10,
    "list": [
      {"id": "pool-1", "name": "云池1"},
      {"id": "pool-2", "name": "云池2"}
    ]
  }
}
```

**异常响应**

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 500 | 服务器内部错误 | `{"code": 500, "message": "获取云池列表时出错: 具体错误信息", "data": null}` |

---

## 2. 任务执行

### 2.1 执行加固任务

**接口信息**

| 属性 | 值 |
|------|-----|
| 接口地址 | `/cu-concrete/execute-playbook/` |
| 请求方法 | POST |
| Content-Type | application/json |
| 功能描述 | 创建并执行加固任务 |

**请求参数（URL 查询参数）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pool_id | string | 是 | 云池ID，例如: pool-1, pool-2, pool-3 |

**请求示例**

```http
POST /cu-concrete/execute-playbook/?pool_id=pool-1
```

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码 |
| message | string | 响应消息 |
| data.task_id | string | 任务ID（格式：YYYYMMDD-随机码） |
| data.pool_id | string | 云池ID |
| data.pool_name | string | 云池名称 |
| data.status | string | 任务状态（running/completed/failed） |

**成功响应示例（200）**

```json
{
  "code": 200,
  "message": "任务已提交",
  "data": {
    "task_id": "20240311-abc123",
    "pool_id": "pool-1",
    "pool_name": "云池1",
    "status": "running"
  }
}
```

**异常响应**

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 400 | 缺少pool_id参数 | `{"code": 400, "message": "缺少pool_id参数", "data": null}` |
| 400 | 无效的云池ID | `{"code": 400, "message": "无效的云池ID: pool-xxx", "data": null}` |
| 409 | 云池正在执行其他任务 | `{"code": 409, "message": "云池 pool-1 正在执行其他任务，请稍后再试", "data": null}` |
| 500 | 服务器内部错误 | `{"code": 500, "message": "提交任务时发生错误: 具体错误信息", "data": null}` |

---

## 3. 任务查询

### 3.1 获取任务列表

**接口信息**

| 属性 | 值 |
|------|-----|
| 接口地址 | `/cu-concrete/tasks/` |
| 请求方法 | GET |
| 功能描述 | 获取任务列表，支持分页 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| current | int | 否 | 当前页码，默认1 |
| pageSize | int | 否 | 每页数量，默认10 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.count | int | 总记录数 |
| data.pageIndex | int | 当前页码 |
| data.pageSize | int | 每页大小 |
| data.list | array | 任务对象数组 |

**list 数组中每个对象的字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务ID |
| pool_id | string | 云池ID |
| pool_name | string | 云池名称 |
| status | string | 任务状态 |

**成功响应示例（200）**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "count": 100,
    "pageIndex": 1,
    "pageSize": 10,
    "list": [
      {
        "task_id": "20240311-abc123",
        "pool_id": "pool-1",
        "pool_name": "云池1",
        "status": "completed"
      }
    ]
  }
}
```

**异常响应**

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 500 | 服务器内部错误 | `{"code": 500, "message": "获取任务列表时出错: 具体错误信息", "data": null}` |

---

### 3.2 获取任务详情

**接口信息**

| 属性 | 值 |
|------|-----|
| 接口地址 | `/cu-concrete/task-detail/` |
| 请求方法 | GET |
| 功能描述 | 获取单个任务的详细信息 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务ID |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.task_id | string | 任务ID |
| data.pool_id | string | 云池ID |
| data.pool_name | string | 云池名称 |
| data.status | string | 任务状态（running/completed/failed） |
| data.created_at | string | 创建时间 |
| data.completed_at | string | 完成时间 |
| data.result_file | string | 结果文件路径 |
| data.total_hosts | int | 主机数 |
| data.policy_names | array | 加固策略中文名称列表 |
| data.script_name | string | 脚本名称 |

**成功响应示例（200）**

```
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "task_id": "20240311-abc123",
    "pool_id": "pool-1",
    "pool_name": "云池1",
    "status": "completed",
    "created_at": "2024-03-11T12:34:56",
    "completed_at": "2024-03-11T12:35:30",
    "result_file": "/opt/cu-concrete/data/results/result_20240311-abc123.csv",
    "total_hosts": 2,
    "policy_names": ["uid为0用户检查"],
    "script_name": "harden.yml"
  }
}
```

**异常响应**

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 400 | 缺少task_id参数 | `{"code": 400, "message": "缺少task_id参数", "data": null}` |
| 404 | 任务不存在 | `{"code": 404, "message": "任务 20240311-abc123 不存在", "data": null}` |
| 500 | 服务器内部错误 | `{"code": 500, "message": "获取任务状态时出错: 具体错误信息", "data": null}` |

---

### 3.3 获取任务日志

**接口信息**

| 属性 | 值 |
|------|-----|
| 接口地址 | `/cu-concrete/task-logs/` |
| 请求方法 | GET |
| 功能描述 | 获取任务执行日志 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务ID |
| lines | int | 否 | 返回日志行数 |

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.task_id | string | 任务ID |
| data.lines | int | 返回行数 |
| data.content | array | 日志行列表 |

**成功响应示例（200）**

```
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "task_id": "20240311-abc123",
    "lines": 50,
    "content": [
      "[12:34:56] 开始执行云池 pool-1 的加固任务",
      "[12:34:56] Playbook路径: /path/to/playbook.yml",
      "[12:35:30] 任务执行完成"
    ]
  }
}
```

**异常响应**

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 400 | 缺少task_id参数 | `{"code": 400, "message": "缺少task_id参数", "data": null}` |
| 404 | 任务不存在 | `{"code": 404, "message": "任务 20240311-abc123 不存在", "data": null}` |
| 500 | 服务器内部错误 | `{"code": 500, "message": "获取任务日志时出错: 具体错误信息", "data": null}` |

---

## 4. 结果查询

### 4.1 获取执行结果

**接口信息**

| 属性 | 值 |
|------|-----|
| 接口地址 | `/cu-concrete/get-results/` |
| 请求方法 | GET |
| 功能描述 | 获取加固结果CSV文件内容，支持分页 |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务ID |
| current | int | 否 | 当前页码，默认1 |
| pageSize | int | 否 | 每页大小，默认10 |

**参数说明**

`task_id` 参数用于指定要查询的任务，系统会自动定位到对应的结果文件。

**响应参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.count | int | 总记录数 |
| data.pageIndex | int | 当前页码 |
| data.pageSize | int | 每页大小 |
| data.list | array | 结果数据列表 |

**成功响应示例（200）**

```
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "count": 100,
    "pageIndex": 1,
    "pageSize": 10,
    "list": [
      {
        "timestamp": "20230101-123456",
        "host": "example-host",
        "dep_id": "1",
        "status": "已加固",
        "module_name": "安全模块名称"
      }
    ]
  }
}
```

**异常响应**

| 状态码 | 场景 | 响应示例 |
|--------|------|----------|
| 400 | 缺少file参数 | `{"code": 400, "message": "缺少file参数", "data": null}` |
| 400 | 无效的文件路径 | `{"code": 400, "message": "无效的文件路径", "data": null}` |
| 404 | 文件不存在 | `{"code": 404, "message": "文件不存在", "data": null}` |
| 500 | 服务器内部错误 | `{"code": 500, "message": "获取结果文件时出错: 具体错误信息", "data": null}` |

---

## 附录

### A. 状态码说明

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 操作成功/查询成功 | 正常业务处理成功 |
| 201 | 创建成功 | 资源创建成功 |
| 400 | 请求参数错误 | 缺少参数、参数格式错误、参数无效 |
| 401 | 未授权访问 | 需要身份认证（预留） |
| 403 | 权限不足 | 无权限执行操作（预留） |
| 404 | 资源不存在 | 任务不存在、文件不存在 |
| 409 | 操作冲突 | 云池正在执行其他任务 |
| 429 | 请求过于频繁 | 限流场景（预留） |
| 500 | 服务器内部错误 | 服务器异常、未捕获的错误 |

### B. 任务状态说明

| 状态 | 说明 |
|------|------|
| running | 执行中 |
| completed | 已完成 |
| failed | 执行失败 |

### C. 数据存储路径

| 数据类型 | 存储路径 |
|----------|----------|
| 任务基本信息 | `/opt/cu-concrete/data/tasks.json` |
| 任务日志 | `/opt/cu-concrete/data/logs/{task_id}.log` |
| 加固结果 | `/opt/cu-concrete/results/result_{task_id}.csv` |
| 原始数据 | `/var/cu-concrete-result/cu-concrete-{task_id}/` |

### D. 接口汇总

| 接口 | 方法 | 功能 |
|------|------|------|
| `/cu-concrete/pool-list/` | GET | 获取云池列表 |
| `/cu-concrete/execute-playbook/` | POST | 执行加固任务 |
| `/cu-concrete/tasks/` | GET | 获取任务列表 |
| `/cu-concrete/task-detail/` | GET | 获取任务详情 |
| `/cu-concrete/task-logs/` | GET | 获取任务日志 |
| `/cu-concrete/get-results/` | GET | 获取执行结果 |

### E. 错误码速查表

| 接口 | 400 | 404 | 409 | 500 |
|------|-----|-----|-----|-----|
| `/cu-concrete/pool-list/` | - | - | - | ✓ |
| `/cu-concrete/execute-playbook/` | ✓（缺少参数、无效云池ID） | - | ✓（云池冲突） | ✓ |
| `/cu-concrete/tasks/` | - | - | - | ✓ |
| `/cu-concrete/task-detail/` | ✓（缺少task_id） | ✓（任务不存在） | - | ✓ |
| `/cu-concrete/task-logs/` | ✓（缺少task_id） | ✓（任务不存在） | - | ✓ |
| `/cu-concrete/get-results/` | ✓（缺少file、无效路径） | ✓（文件不存在） | - | ✓ |

**说明：**
- `400` - 请求参数错误（缺少必填参数、参数格式错误、参数值无效）
- `404` - 资源不存在（任务不存在、文件不存在）
- `409` - 操作冲突（云池正在执行其他任务）
- `500` - 服务器内部错误（未捕获的异常、系统错误）

---

**文档结束**