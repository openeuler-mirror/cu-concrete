# 任务管理器说明

负责任务创建、状态流转、日志与结果汇总：

- 内存任务表 + 文件持久化
- 与备份目录 `cu-concrete-{task_id}` 联动
- 提供 combine/csv 等结果处理入口

详见 `task_manager.py` 中各公开函数注释。
