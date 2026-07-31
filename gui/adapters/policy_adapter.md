# policy_adapter

按策略目录名动态加载现有策略类，转调 check/fix/rollback/reset。
捕获异常并转为 ActionResult，避免冲垮 GUI 主循环。
