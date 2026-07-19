# API 模块总览

本目录为 cu-concrete 的 Django API 应用（`api`）。

## 模块一览

| 文件 | 职责 |
|------|------|
| `views.py` | HTTP 接口实现 |
| `urls.py` | 路由注册 |
| `eventbus.py` | 配置读写事件总线（单例+锁） |
| `task_manager.py` | 加固任务生命周期 |
