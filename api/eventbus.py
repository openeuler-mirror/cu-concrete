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
    
    def eventbus_get_pool_hosts(self, pool_id, config_name=None):
        """
        读方法：获取云池机器列表（由后端解析 inventory 文件，前端不做解析）
        config_name 为空时取云池自身 inventory，传入时取该安全配置对应的 inventory
        """
        try:
            hosts = get_pool_hosts(pool_id, config_name)
            return CommonResponses.QUERY_SUCCESS({
                'count': len(hosts),
                'pool_id': pool_id,
                'config_name': config_name,
                'list': hosts
            })
        except Exception as e:
            logger.error(f"获取机器列表时出错: {str(e)}")
            return ApiResponse.error(f'获取机器列表时出错: {str(e)}', 500)
