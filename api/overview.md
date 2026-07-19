# 架构与模块关系

## 分层

1. **路由层** `urls.py` → 映射 path 到 view
2. **接口层** `views.py` → 参数校验、Swagger、调用业务
3. **事件总线** `eventbus.py` → 聚合 conf 读写并加锁
4. **任务层** `task_manager.py` → 异步任务与结果归档
5. **工具层** `conf_utils.py` / `response_utils.py`

## 数据流（简图）

```
Client → urls → views → eventbus/task_manager → conf_utils / 文件系统
```


---

## 摘录：平台接口文档（开头）

# cu-concrete 接口文档

本文档描述了 cu-concrete 安全合规检查与加固平台的所有 API 接口。

- **版本**：v1.0
- **日期**：2026-03-16
- **Base URL**：`http://127.0.0.1:8000`

---
