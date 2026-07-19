# 架构与模块关系

## 分层

1. **路由层** `urls.py` → 映射 path 到 view
2. **接口层** `views.py` → 参数校验、Swagger、调用业务
3. **事件总线** `eventbus.py` → 聚合 conf 读写并加锁
4. **任务层** `task_manager.py` → 异步任务与结果归档
5. **工具层** `conf_utils.py` / `response_utils.py`

