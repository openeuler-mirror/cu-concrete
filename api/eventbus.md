# 事件总线设计说明

`Eventbus` 采用单例模式，为配置相关写操作提供独立锁：

- `save_conf_content_lock`
