# 事件总线设计说明

`Eventbus` 采用单例模式，为配置相关写操作提供独立锁：

- `save_conf_content_lock`
- `delete_conf_lock`
- `generate_config_lock`
- `save_generated_config_lock`

读方法直接委托 `conf_utils`；写方法在 `with lock` 中执行，避免并发写坏配置。
