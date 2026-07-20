# 做事件总线, 实现功能：
# 1、使用单例模式
# 2、实现事业部 和 公司层 的加固项匹配
# 3、生成ansible脚本 并生成记录

from rest_framework.response import Response
from rest_framework import status
import threading
import os
import time
from .conf_utils import *
# 导入统一响应工具
from .response_utils import ApiResponse, CommonResponses


class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

class Eventbus(Singleton):
    def __init__(self):
        # 双重校验，避免重复初始化
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 两个独立的写锁
        self.save_conf_content_lock = threading.Lock()
        self.delete_conf_lock = threading.Lock()
        self.generate_config_lock = threading.Lock()
        self.save_generated_config_lock = threading.Lock()

    def eventbus_pool_list(self, request):
        """
        读方法：查找云池列表信息
        """
        return pool_list(request)
        
    def eventbus_find_pool_configs(self, pool_name):
        """
        读方法：查找某云池内所有配置信息
        """
        return find_pool_configs(pool_name)
    def eventbus_get_level_conf(self, harden_models):
        """
        读方法：获取级别配置信息
        """
        try:
            return get_level_conf(harden_models)
        except Exception as e:
            logger.error(f"获取配置内容时出错: {str(e)}", exc_info=True)
            return ApiResponse.error(f'获取级别配置信息时出错: {str(e)}', 500)
    
    def eventbus_get_config_content(self, pool_id, config_name):
        """
        读方法：获取配置文件内容
        """
        print("执行-eventbus_get_config_content")
        try:
            # 调用conf_utils中的函数，传递两个参数
            return find_config_content(pool_id, config_name)
        except Exception as e:
            logger.error(f"获取配置内容时出错: {str(e)}", exc_info=True)
            return ApiResponse.error(f'获取配置内容时出错: {str(e)}', 500)

    def eventbus_save_conf_content(self, pool_id, config_name, ini_content, yml_content):
        """
