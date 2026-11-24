# cu-concrete 接口文档

本文档描述 cu-concrete 当前代码（`api/urls.py` + `api/views.py`）实际提供的全部 API。

- **版本**：v2.0
- **日期**：2026-11-03
- **Base URL**：`http://127.0.0.1:8000/cu-concrete/`
- **在线文档**：Swagger `/swagger/`　ReDoc `/redoc/`
- **前端页面**：`GET /`（渲染 `templates/index.html`）

---

## 1. 通用约定

### 1.1 响应结构

```json
{ "code": 200, "message": "查询成功", "data": {} }
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 业务状态码，200 表示成功 |
| message | string | 响应消息 |
| data | object/null | 业务数据 |

### 1.2 分页

分页接口统一用 `current`（页码，默认 1）和 `pageSize`（每页条数），响应 `data` 内含 `count` / `pageIndex` / `pageSize` / `list`。

各接口对 `pageSize` 的处理**并不一致**，需注意：

| 接口 | 不传 pageSize | 传非法值（非数字或 ≤0） |
|------|---------------|------------------------|
| `/pool-list/` | 返回全部云池 | 回落为全部云池 |
| `/tasks/` | 10 | **直接报错，返回 500** |
| `/get-results/` | 返回全部结果行 | 回落为 10 |

### 1.3 错误处理

| code | 含义 | 典型场景 |
|------|------|----------|
| 400 | 请求参数错误 | 缺少参数、参数值无效 |
| 404 | 资源不存在 | 任务 / 配置 / 云池 / 文件不存在 |
| 405 | 方法不允许 | 接口仅支持特定方法 |
| 409 | 操作冲突 | 云池正在执行其他任务 |
| 500 | 服务器内部错误 | 未捕获异常，或业务规则失败（如配置重名） |

参数类错误的 message 统一格式：

- 缺少参数：`缺少必要参数: {参数名}`
- 参数无效：`无效参数: {说明}`

> **两点重要差异**
>
> 1. 部分错误分支只设置了响应体的 `code`，HTTP 状态码仍为 500。**前端应以响应体的 `code` 判断业务结果，不要依赖 HTTP 状态码。**
> 2. 请求方法不在接口允许列表内时，由 Django REST Framework 直接返回 HTTP 405，响应体为 `{"detail": "Method \"XXX\" not allowed."}`，**不符合上述统一封装**。

---

## 2. 接口速查表

| 接口 | 方法 | 功能 |
|------|------|------|
| `/pool-list/` | GET | 获取云池列表 |
| `/pool-hosts/` | GET | 获取云池机器列表 |
| `/execute-playbook/` | POST | 执行加固任务 |
| `/tasks/` | GET | 获取任务列表 |
| `/task-detail/` | GET | 获取任务详情 |
| `/task-logs/` | GET | 获取任务日志 |
| `/get-results/` | GET | 获取执行结果 |
| `/harden-items/` | GET | 获取加固项列表 |
| `/get-conf-level/` | GET | 获取公司级/部门级加固项映射 |
| `/generate-config/` | POST | 生成配置文件（预览） |
| `/save-generated-config/` | POST | 保存生成的配置 |
| `/from-pool-get-configs/` | GET/POST | 获取云池下的配置列表 |
| `/from-file-get-config/` | GET/POST | 获取配置内容 |
| `/save-conf-content/` | POST | 保存配置内容 |
| `/delete-config/` | POST | 删除配置 |

---

## 3. 云池管理

### 3.1 获取云池列表

`GET /cu-concrete/pool-list/`

数据源：`api/conf_cloud_pools_info.yaml`，每次请求读盘，修改后立即生效。

**参数**（query，均选填）

| 参数 | 类型 | 说明 |
|------|------|------|
| current | int | 页码，默认 1 |
| pageSize | int | 每页条数，默认返回全部 |

**返回 data**

| 字段 | 说明 |
|------|------|
| count / pageIndex / pageSize | 分页信息 |
| list[].id | 云池ID |
| list[].name | 云池名称 |
| list[].desc | 云池描述 |
| list[].machineCount | 该云池下的机器数量 |

**错误**

| HTTP | code | message |
|------|------|---------|
| 500 | 500 | `获取云池列表时出错: {具体错误信息}` |

> 云池定义与安全配置记录（`api/conf_data.json`）是两份独立数据，数量可以不一致。

### 3.2 获取云池机器列表

`GET /cu-concrete/pool-hosts/`

**参数**（query）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pool_id | string | 是 | 云池ID |
| config_name | string | 否 | 安全配置文件名。不传读云池台账 `machines`；传入则解析该配置对应的 inventory 文件 |

**返回 data**

| 字段 | 说明 |
|------|------|
| count | 机器数量 |
| pool_id | 云池ID |
| config_name | 本次使用的配置名，未传时为 `null` |
| list[].name | 主机名（未填主机名时与 ip 相同） |
| list[].ip | 机器IP |

**解析规则**：传 `config_name` 时逐行解析 inventory，跳过空行、`#`/`;` 注释行、`[xxx]` 组定义行、含 `=` 的变量行，其余按空白切分取 `ip` 与 `name`。**配置记录不存在或解析结果为空时，静默回退到云池台账的 `machines`**。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: pool_id` |
| 404 | 404 | `云池 {pool_id} 不存在` |
| 500 | 500 | `获取机器列表时出错: {具体错误信息}` |

---

## 4. 任务执行

### 4.1 执行加固任务

`POST /cu-concrete/execute-playbook/`

创建异步加固任务：同一云池串行互斥，不同云池并行。机器清单与执行脚本一律取自所选安全配置。

**参数**（全部在 **query**，非 body）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pool_id | string | 是 | 云池ID |
| config_name | string | 是 | 安全配置文件名，如 `playbook_abc123.yml` |

**返回 data**

| 字段 | 说明 |
|------|------|
| task_id | 任务ID（格式 `YYYYMMDD-随机码`） |
| status | 创建后固定为 `running` |
| pool_id / pool_name | 云池ID / 云池名称 |
| config_name | 本次执行使用的配置名 |

message 为 `任务已提交`。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: pool_id` |
| 400 | 400 | `缺少必要参数: config_name` |
| 400 | 400 | `无效参数: 无效的云池ID: {pool_id}` |
| 404 | 404 | `云池 {pool_id} 中未找到安全配置: {config_name}` |
| 404 | 404 | `安全配置 {config_name} 的配置文件缺失，无法执行` |
| 409 | 409 | `云池 {pool_id} 正在执行其他任务，请稍后再试` |
| 500 | 500 | `提交任务时发生错误: {具体错误信息}` |

---

## 5. 任务查询

### 5.1 获取任务列表

`GET /cu-concrete/tasks/`

按创建时间倒序返回。

**参数**（query，均选填）：`current`（默认 1）、`pageSize`（默认 10）

**任务对象字段**（5.2 返回同一结构）

| 字段 | 说明 |
|------|------|
| task_id | 任务ID |
| pool_id / pool_name | 云池ID / 名称 |
| config_name | 本次执行使用的配置名 |
| status | `running` / `completed` / `failed` |
| created_at / completed_at | 创建时间 / 完成时间（ISO 格式） |
| error_message | 失败原因 |
| result_file | 结果文件路径 |
| total_hosts | 结果中的主机数 |
| timestamp | 任务执行标识（当前恒为 `null`） |
| policy_names[] | 加固策略名称列表 |
| script_name | 实际执行的脚本名 |

**错误**

| HTTP | code | message |
|------|------|---------|
| 500 | 500 | `获取任务列表时出错: {具体错误信息}` |

> `current` / `pageSize` 传非数字会直接抛错并返回 500。

### 5.2 获取任务详情

`GET /cu-concrete/task-detail/`

**参数**（query）：`task_id`（必填）

**返回 data**：任务对象全字段（同 5.1），message 为 `查询成功`。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: task_id` |
| 404 | 404 | `任务 {task_id} 不存在` |
| 500 | 500 | `获取任务状态时出错: {具体错误信息}` |

### 5.3 获取任务日志

`GET /cu-concrete/task-logs/`

**参数**（query）：`task_id`（必填）

**返回 data**

| 字段 | 说明 |
|------|------|
| task_id | 任务ID |
| content | 日志内容，**单个字符串**，多行以 `\n` 分隔 |

服务端每个任务最多保留 1000 行日志，超出后丢弃最早的行。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: task_id` |
| 404 | 404 | `任务 {task_id} 不存在` |
| 500 | 500 | `获取任务日志时出错: {具体错误信息}` |

---

## 6. 结果查询

### 6.1 获取执行结果

`GET /cu-concrete/get-results/`

读取任务结果 CSV 并转为 JSON。

**参数**（query）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 支持 `20261016-abc123`、`result_20261016-abc123`、`result_20261016-abc123.csv` |
| current | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，不传返回全部 |

**结果文件定位**：固定为 `/opt/cu-concrete/data/results/result_{task_id}.csv`，并校验路径必须位于 `/opt/cu-concrete` 下（防目录穿越）。

**返回 data**：`count` / `pageIndex` / `pageSize` / `list`，`list` 元素取自 CSV 表头。

**CSV 表头**：`task_id`、`host`、`dep_id`、`status`、`module_name`，其中 `status` 取值为 `未加固` / `加固失败` / `已加固`。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: task_id` |
| 500 | 400 | `无效的文件路径` |
| 404 | 404 | `文件不存在` |
| 500 | 500 | `获取结果文件时出错: {具体错误信息}` |

---

## 7. 配置管理

### 7.1 获取加固项列表

`GET /cu-concrete/harden-items/`

无参数。扫描下列目录下的策略 YAML：

| 目录 | category |
|------|----------|
| `department_1_policy` | 系统安全 |
| `department_2_policy` | 容器安全 |
| `department_3_policy` | 应用安全 |

> `default_0_policy` **不在扫描范围内**；目录不存在时跳过，当前仓库无 `department_3_policy`，实际只有前两类。

**返回 data**：`count`、`list`（不分页，无 `pageIndex`/`pageSize`）。列表按 `(dep, item_id)` 升序。

| 字段 | 说明 |
|------|------|
| id | 目录名，如 `Items_01_SetEmptyAccountPwd` |
| name | 加固项名称（取 YAML 的 `description`） |
| description | 加固项描述 |
| category | 系统安全 / 容器安全 / 应用安全 |
| dep | 部门编号（YAML 顶层 `dep`） |
| item_id | 加固项编号（YAML 顶层 `id`） |

> 条目取目录内**第一个** YAML 文件；YAML 无 `description` 键时该条目被跳过。
> `dep` 与 `item_id` 拼接后的值用于结果过滤（例：`2` + `12` → `212`）。

**错误**

| HTTP | code | message |
|------|------|---------|
| 500 | 500 | `获取加固项列表时出错: {具体错误信息}` |

### 7.2 获取加固级别配置

`GET /cu-concrete/get-conf-level/`

**参数**（query）：`harden_models`（必填），只能为 `harden-company-model` 或 `harden-department-model`，数据源 `api/conf_harden.json`。

**返回 data**：`harden_items`（数组，元素格式 `{dep}_{item_id}`，如 `1_1`）

> 该接口 message 为 `success`（非 `查询成功`）。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `无效的模型类型，必须是 harden-company-model 或 harden-department-model` |
| 405 | 405 | `方法不允许，只支持 GET 请求` |
| 500 | 500 | `获取级别配置信息时出错: {具体错误信息}` |

### 7.3 生成配置文件（预览）

`POST /cu-concrete/generate-config/`

按云池、机器、加固项生成 inventory.ini 与 playbook.yml 内容，**仅预览，不落库**。

**参数**（body，JSON；四项均必填，校验顺序 `pool_id` → `hosts` → `harden_model` → `harden_items`）

| 参数 | 类型 | 说明 |
|------|------|------|
| pool_id | string | 云池ID |
| hosts | array | 机器列表，元素为 `{ip, name}` 或 IP 字符串 |
| harden_items | array | 加固项数组，格式 `{dep}_{item_id}`，如 `["1_1","2_12"]` |
| harden_model | string | `harden-company-model` / `harden-department-model` / `custom-model` |

**返回 data**

| 字段 | 说明 |
|------|------|
| ini_file / yml_file | 生成的文件路径（**预览后即被删除，仅供展示**） |
| ini_content / yml_content | 文件内容 |
| hosts_count | 机器数量 |
| harden_items | 逗号拼接的加固项字符串，如 `1_1,1_2` |

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: {参数名}` |
| 500 | 500 | `配置生成异常：: {具体错误信息}` |

### 7.4 保存生成的配置文件

`POST /cu-concrete/save-generated-config/`

将生成内容写入磁盘，并登记到 `api/conf_data.json`。

**参数**（body，JSON；均必填，校验顺序 `pool_id` → `hosts` → `harden_model` → `harden_items` → `generate_person_name` → `config_name` → `ini_content` → `yml_content`）

| 参数 | 类型 | 说明 |
|------|------|------|
| pool_id | string | 云池ID |
| config_name | string | 配置名称（作为 playbook 文件名，需唯一） |
| hosts | array | 机器列表 |
| harden_items | array | 加固项数组 |
| harden_model | string | 加固模式 |
| generate_person_name | string | 配置生成人姓名 |
| ini_content / yml_content | string | inventory / playbook 内容 |

**返回 data**：`ini_file`、`yml_file`、`hosts_count`、`harden_items`（数组）、`harden_items_str`（逗号拼接字符串）

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: {参数名}` |
| 500 | 500 | `配置文件名已存在, 请更换名称！` |
| 500 | 500 | `配置保存异常：{具体错误信息}` |

### 7.5 获取云池下的配置列表

`GET` 或 `POST /cu-concrete/from-pool-get-configs/`

**参数**：`pool_id`（必填）。GET 传 query，POST 传 body。

**返回 data**：`count`、`pageIndex`（固定 1）、`pageSize`（等于配置数量）、`list`

| 字段 | 说明 |
|------|------|
| list[].id | 配置文件全名（作为后续接口的 `config_name`） |
| list[].name | 文件名按下划线切分后取前两段重拼 |
| list[].description | `生成于 {generateTime}`，无时间时为 `生成于 未知时间` |

按生成时间倒序返回，最新生成的排在最前，无生成时间的排最后。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: pool_id` |
| 500 | 404 | `配置文件 {绝对路径} 不存在` |
| 500 | 500 | `获取所有配置文件名时出错: {具体错误信息}` |

> 该云池下没有任何配置属于正常业务状态：返回 200 + `count: 0` + 空 `list`。

### 7.6 获取配置内容

`GET` 或 `POST /cu-concrete/from-file-get-config/`

**参数**：`pool_id`（必填）、`config_name`（必填）。GET 传 query，POST 传 body。

**返回 data**：`ini_file`、`yml_file`、`ini_content`、`yml_content`，message 为 `操作成功`。

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: pool_id` |
| 400 | 400 | `缺少必要参数: config_name` |
| 500 | 404 | `配置文件 {绝对路径} 不存在` |
| 500 | 404 | `未找到云池：{pool_id}` |
| 500 | 404 | `云池 {pool_id} 中未找到配置文件：{config_name}` |
| 500 | 500 | `获取配置文件内容时出错: {具体错误信息}` |

### 7.7 保存配置内容

`POST /cu-concrete/save-conf-content/`

保存手工修改后的 ini / yml 内容，并刷新该配置的生成时间。**请求体必须是合法 JSON**（用 `json.loads(request.body)` 解析）。

**参数**（body）：`pool_id`、`config_name`、`ini_content`、`yml_content`（均必填）

**返回 data**：`pool_name`（值为传入的 `pool_id`）、`config_name`

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数`（不带参数名） |
| 405 | 405 | `方法不允许` |
| 500 | 404 | `配置数据库 {绝对路径} 不存在` |
| 500 | 400 | `INI配置文件路径无效: {path}` |
| 500 | 400 | `YML配置文件路径无效: {path}` |
| 500 | 500 | `服务器错误: {具体错误信息}` |

### 7.8 删除配置

`POST /cu-concrete/delete-config/`

从配置数据库中删除记录，**不删除磁盘上的 ini/yml 文件**。

**参数**（body，JSON）：`pool_id`、`config_name`（均必填）

**返回 data**：`pool_id`、`config_name`

**错误**

| HTTP | code | message |
|------|------|---------|
| 400 | 400 | `缺少必要参数: pool_id 或 config_name` |
| 500 | 404 | `配置数据库 {绝对路径} 不存在` |
| 500 | 404 | `未找到云池 {pool_id} 的配置记录` |
| 500 | 404 | `云池 {pool_id} 中未找到配置文件 {config_name}` |
| 500 | 405 | `方法不允许` |
| 500 | 500 | `删除配置时出错: {具体错误信息}` |

---

## 8. 附录

### 8.1 任务状态

| 状态 | 说明 |
|------|------|
| running | 执行中 |
| completed | 已完成 |
| failed | 执行失败 |

### 8.2 加固状态（结果 CSV）

| status | 说明 |
|--------|------|
| 未加固 | 策略未执行 |
| 加固失败 | 策略执行失败 |
| 已加固 | 策略执行成功 |

### 8.3 数据存储路径

| 数据类型 | 存储路径 |
|----------|----------|
| 任务基本信息 | `/opt/cu-concrete/data/tasks.json` |
| 任务日志 | `/opt/cu-concrete/data/logs/{task_id}.log` |
| 加固结果 CSV | `/opt/cu-concrete/data/results/result_{task_id}.csv` |
| 原始备份数据 | `/opt/cu-concrete/data/backup/cu-concrete-{task_id}/`（结果合并成功后自动删除） |
| 云池与机器台账 | `api/conf_cloud_pools_info.yaml` |
| 安全配置数据库 | `api/conf_data.json` |
| 加固级别映射 | `api/conf_harden.json` |
| inventory 模板 | `data/fetch/fetch_template.ini` |
| playbook 模板 | `data/fetch/playbook_template.yml` |
| 生成的安全配置文件 | `data/fetch/{pool_id}/inventory_{key}.ini`、`data/fetch/{pool_id}/{config_name}` |

### 8.4 本版修正记录

| 项 | 旧文档 | 实际 |
|----|--------|------|
| `pageSize` 非法值 | 统一回落 10 | `pool-list/` 回落为全部；`get-results/` 回落 10；`tasks/` 直接 500 |
| `save-conf-content/` 配置库不存在 | code 400 | code 404 |
| 404 类 message | `配置文件 api/conf_data.json 不存在` | 为**绝对路径** `配置文件 {绝对路径} 不存在` |
| `harden-items/` 扫描范围 | 未说明 | 不含 `default_0_policy`，且当前无 `department_3_policy` |
| `generate-config/` 必填项 | 3 项 | 4 项（缺 `harden_model`） |
| `from-pool-get-configs/` 的 `name` | `playbook_abc123` | `playbook_abc123.yml` |
| 方法不允许的响应体 | 统一封装 | DRF 返回 `{"detail": "Method \"XXX\" not allowed."}` |

---

**文档结束**
