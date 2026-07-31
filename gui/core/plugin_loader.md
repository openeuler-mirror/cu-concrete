# plugin_loader

扫描 `plugins/**/plugin.yaml`，动态加载 `plugin.py` 中的入口类并注册。
加载失败时跳过该插件并记录错误，不影响其它插件。
